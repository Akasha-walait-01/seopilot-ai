# This file is our website crawler
# It uses Playwright (real Chromium browser) so JavaScript-rendered
# pages (React, Next.js, Vue, etc) are fully loaded before we read the HTML
# Falls back gracefully and records errors instead of crashing
#
# CRITICAL FIX: Playwright's sync API only works reliably in the actual
# main thread of a process. FastAPI dispatches sync route handlers (like
# our crawl endpoint) into a background threadpool worker thread - NOT
# the main thread - so even setting WindowsProactorEventLoopPolicy inside
# that worker thread does not fix the "NotImplementedError" when Chromium
# tries to launch as a subprocess. The only reliable fix is to run the
# actual Playwright crawl in a completely separate child PROCESS (via
# multiprocessing), which gets its own real main thread where the
# Proactor policy works as expected. This keeps crawl_website()'s public
# signature identical, so no other file needs to change.

import sys
import time
import multiprocessing
from queue import Empty
import requests
from urllib.parse import urljoin, urlparse
from urllib import robotparser
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# safety limits (rule from spec section 34: crawl limits, timeouts, SSRF protection)
MAX_PAGES_DEFAULT = 10
SAFETY_MAX_PAGES = 5000  # hard internal ceiling, not a normal limit - prevents runaway crawls only
PAGE_TIMEOUT_MS = 40000  # 40 seconds per page, some sites are slow to render
CRAWL_DELAY_SECONDS = 1  # simple rate limiting, be polite to the target server
MAX_RETRIES_PER_PAGE = 1  # retry once if a page fails (helps with flaky sites)

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# headers used only for robots.txt / sitemap checks (plain http request, no browser needed)
ROBOTS_HEADERS = {"User-Agent": BROWSER_USER_AGENT}

# resource types we block to make crawling faster
# we still need html, css (for layout-driven content) and scripts (to render JS)
# but images/fonts/media are not needed for SEO text extraction
BLOCKED_RESOURCE_TYPES = {"image", "font", "media"}

# a small script injected into every page to reduce the chance of sites
# detecting this as an automated browser (some sites like Medium slow
# down or block requests when they detect automation flags)
STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
"""


def normalize_domain(netloc: str) -> str:
    # treat "www.example.com" and "example.com" as the same domain
    return netloc.lower().removeprefix("www.")


def is_same_domain(site_domain: str, target_url: str) -> bool:
    # compares a link against the ORIGINAL site domain (not the current
    # page's domain). This prevents the crawler from following a chain of
    # redirects onto a completely different website (domain drift bug)
    target_domain = normalize_domain(urlparse(target_url).netloc)
    return site_domain == target_domain


def can_crawl(url: str, session: requests.Session) -> bool:
    # check robots.txt before crawling a page
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        response = session.get(robots_url, timeout=10)
        rp = robotparser.RobotFileParser()
        rp.parse(response.text.splitlines())
        return rp.can_fetch(BROWSER_USER_AGENT, url)
    except Exception:
        # if robots.txt cannot be read, allow crawling by default
        return True


def clean_url(url: str) -> str:
    # remove fragment identifiers and trailing slash so the same page
    # is not queued twice under slightly different url strings
    url = url.split("#")[0]
    if url.endswith("/") and url.count("/") > 3:
        url = url.rstrip("/")
    return url


def _extract_date(soup: BeautifulSoup, meta_props: list[str], itemprop_name: str) -> str | None:
    # tries several common ways sites mark publish/modified dates,
    # in order of reliability. Returns None if nothing is found -
    # never guesses a date.
    for prop in meta_props:
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        if tag and tag.get("content"):
            return tag.get("content")

    itemprop_tag = soup.find(attrs={"itemprop": itemprop_name})
    if itemprop_tag:
        value = itemprop_tag.get("datetime") or itemprop_tag.get("content") or itemprop_tag.get_text(strip=True)
        if value:
            return value

    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        return time_tag.get("datetime")

    return None


def _detect_author_signal(soup: BeautifulSoup) -> bool:
    # heuristic check for any common author/byline marker on the page.
    # This is a signal for E-E-A-T review, not a guarantee of a real author.
    if soup.find(attrs={"rel": "author"}):
        return True
    if soup.find(attrs={"itemprop": "author"}):
        return True
    if soup.find("meta", attrs={"name": "author"}):
        return True
    author_class_match = soup.find(class_=lambda c: bool(c) and "author" in " ".join(c if isinstance(c, list) else [c]).lower())
    return bool(author_class_match)


def parse_page(url: str, html: str, status_code: int, site_domain: str) -> dict:
    # extract all SEO-relevant fields from one page's rendered HTML
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None

    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href") if canonical_tag else None

    robots_meta_tag = soup.find("meta", attrs={"name": "robots"})
    robots_meta = robots_meta_tag.get("content") if robots_meta_tag else None

    images = soup.find_all("img")
    images_missing_alt = sum(1 for img in images if not img.get("alt", "").strip())

    # count links, separate internal vs external
    # "internal" means same domain as the ORIGINAL site being crawled,
    # not just the current page (avoids following redirects off-site)
    all_links = soup.find_all("a", href=True)
    internal_links = []
    external_links = []
    for link in all_links:
        href = urljoin(url, link["href"])
        if not href.startswith(("http://", "https://")):
            continue
        if is_same_domain(site_domain, href):
            internal_links.append(href)
        else:
            external_links.append(href)

    text = soup.get_text(separator=" ", strip=True)
    word_count = len(text.split())

    has_schema = bool(soup.find("script", attrs={"type": "application/ld+json"}))

    # --- new fields for E-E-A-T, freshness, and mobile-friendliness checks ---
    viewport_tag = soup.find("meta", attrs={"name": "viewport"})
    has_viewport_meta = bool(viewport_tag)

    published_date = _extract_date(
        soup, ["article:published_time", "og:published_time", "publish_date"], "datePublished"
    )
    modified_date = _extract_date(
        soup, ["article:modified_time", "og:updated_time"], "dateModified"
    )
    author_detected = _detect_author_signal(soup)

    return {
        "url": url,
        "status_code": status_code,
        "title": title,
        "meta_description": meta_description,
        "h1_count": len(h1_tags),
        "h1_text": h1_tags[0] if h1_tags else None,
        "h2_count": len(h2_tags),
        "h3_count": len(h3_tags),
        "canonical": canonical,
        "robots_meta": robots_meta,
        "images_count": len(images),
        "images_missing_alt": images_missing_alt,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "word_count": word_count,
        "has_schema": has_schema,
        "internal_links": list(set(internal_links)),
        "has_viewport_meta": has_viewport_meta,
        "published_date": published_date,
        "modified_date": modified_date,
        "author_detected": author_detected,
        "page_load_time_ms": None,  # filled in by _do_crawl() after fetch
    }


def _broken_page_entry(url: str, error_message: str) -> dict:
    # a placeholder entry used when a page fails to load
    return {
        "url": url,
        "status_code": 0,
        "title": None,
        "meta_description": None,
        "h1_count": 0,
        "h1_text": None,
        "h2_count": 0,
        "h3_count": 0,
        "canonical": None,
        "robots_meta": None,
        "images_count": 0,
        "images_missing_alt": 0,
        "internal_links_count": 0,
        "external_links_count": 0,
        "word_count": 0,
        "has_schema": False,
        "internal_links": [],
        "has_viewport_meta": False,
        "published_date": None,
        "modified_date": None,
        "author_detected": False,
        "page_load_time_ms": None,
        "error": error_message,
    }


def fetch_rendered_page(browser, url: str) -> tuple[str, int, str, str]:
    """
    Open the url in a real browser tab, wait for JavaScript to render,
    and return (html, status_code, final_url_after_redirects, content_type).
    Retries once on timeout, since some sites are simply slow or flaky.
    """
    last_error = None

    for attempt in range(MAX_RETRIES_PER_PAGE + 1):
        page = browser.new_page(user_agent=BROWSER_USER_AGENT)
        page.add_init_script(STEALTH_INIT_SCRIPT)

        # block heavy resources we do not need, to speed up crawling
        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in BLOCKED_RESOURCE_TYPES
            else route.continue_(),
        )

        try:
            # "domcontentloaded" fires once the HTML/JS structure is ready.
            # We avoid "networkidle" as the main wait condition because many
            # sites (analytics, chat widgets, live tracking scripts) never
            # go fully idle, which causes constant timeouts on normal pages.
            response = page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
            status_code = response.status if response else 0
            final_url = page.url
            content_type = response.headers.get("content-type", "") if response else ""

            # give client-side JavaScript a short window to finish rendering
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except PlaywrightTimeoutError:
                pass  # not fully idle yet, proceed with whatever rendered

            # scroll down once, some sites lazy-load navigation links or
            # article cards only after the user scrolls (infinite scroll feeds)
            try:
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(1000)
            except Exception:
                pass

            html = page.content()
            page.close()
            return html, status_code, final_url, content_type

        except PlaywrightTimeoutError as error:
            last_error = error
            page.close()
            if attempt < MAX_RETRIES_PER_PAGE:
                time.sleep(2)  # brief pause before retrying
                continue
            raise last_error

        except Exception as error:
            page.close()
            raise error


def check_site_crawlability(start_url: str) -> dict:
    """
    One-time, site-level check (not per-page): does robots.txt exist and
    is it readable, and does an XML sitemap exist at the common locations.
    Returns real, measured results only - never assumes a sitemap exists.
    Uses plain requests, not Playwright, so this runs fine in any thread.
    """
    parsed = urlparse(start_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    result = {"robots_txt_found": False, "sitemap_found": False, "sitemap_url": None}

    session = requests.Session()
    session.headers.update(ROBOTS_HEADERS)

    try:
        robots_resp = session.get(f"{base}/robots.txt", timeout=10)
        result["robots_txt_found"] = robots_resp.status_code == 200
    except Exception:
        pass

    candidate_sitemaps = [f"{base}/sitemap.xml", f"{base}/sitemap_index.xml", f"{base}/sitemap-index.xml"]
    for sitemap_url in candidate_sitemaps:
        try:
            sitemap_resp = session.get(sitemap_url, timeout=10)
            if sitemap_resp.status_code == 200 and "xml" in sitemap_resp.headers.get("content-type", "").lower():
                result["sitemap_found"] = True
                result["sitemap_url"] = sitemap_url
                break
        except Exception:
            continue

    return result


def _do_crawl(start_url: str, max_pages: int) -> tuple[list[dict], bool]:
    """
    The actual Playwright crawl logic. This function must only ever be
    called from inside _crawl_worker(), i.e. from a fresh child process's
    real main thread - never directly, and never from a thread pool.
    """
    site_domain = normalize_domain(urlparse(start_url).netloc)
    effective_max_pages = min(max_pages, SAFETY_MAX_PAGES) if max_pages else SAFETY_MAX_PAGES

    visited = set()
    to_visit = [start_url]
    results = []

    robots_session = requests.Session()
    robots_session.headers.update(ROBOTS_HEADERS)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            is_first_url = True

            while to_visit and len(visited) < effective_max_pages:
                url = to_visit.pop(0)
                print(f"[CRAWL] Fetching: {url} (visited so far: {len(visited)})", flush=True)

                if url in visited:
                    continue

                # the start_url is always crawled regardless of robots.txt -
                # this is an owner-initiated audit tool, not a public bot.
                # Only later, discovered links respect robots.txt.
                if not is_first_url and not can_crawl(url, robots_session):
                    visited.add(url)
                    continue

                try:
                    fetch_start = time.time()
                    html, status_code, final_url, content_type = fetch_rendered_page(browser, url)
                    load_time_ms = round((time.time() - fetch_start) * 1000, 1)

                    final_url = clean_url(final_url)
                    visited.add(url)
                    visited.add(final_url)

                    if not is_same_domain(site_domain, final_url):
                        is_first_url = False
                        continue

                    if content_type and "text/html" not in content_type:
                        is_first_url = False
                        continue

                    page_data = parse_page(final_url, html, status_code, site_domain)
                    page_data["page_load_time_ms"] = load_time_ms
                    results.append(page_data)
                    print(f"[CRAWL] Success: {final_url}", flush=True)

                    for link in page_data["internal_links"]:
                        link = clean_url(link)
                        if link not in visited and link not in to_visit:
                            to_visit.append(link)

                except PlaywrightTimeoutError:
                    visited.add(url)
                    results.append(_broken_page_entry(
                        url, "Page took too long to load, even after retrying (timeout)."
                    ))
                    print(f"[CRAWL] TIMEOUT: {url}", flush=True)

                except Exception as error:
                    visited.add(url)
                    results.append(_broken_page_entry(url, str(error)))
                    print(f"[CRAWL] FAILED: {url} -> {error}", flush=True)

                is_first_url = False
                time.sleep(CRAWL_DELAY_SECONDS)
        finally:
            browser.close()

    fully_crawled = len(to_visit) == 0
    return results, fully_crawled


def _crawl_worker(start_url: str, max_pages: int, result_queue) -> None:
    """
    Entry point that runs inside a brand-new CHILD PROCESS (via
    multiprocessing), which has its own genuine main thread. Setting the
    Windows Proactor event loop policy here works reliably because this
    is a real main thread, unlike a FastAPI threadpool worker thread.
    """
    try:
        if sys.platform == "win32":
            import asyncio
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        results, fully_crawled = _do_crawl(start_url, max_pages)
        result_queue.put(("ok", results, fully_crawled))
    except Exception as error:
        result_queue.put(("error", str(error), None))


def crawl_website(start_url: str, max_pages: int = MAX_PAGES_DEFAULT) -> tuple[list[dict], bool]:
    """
    PUBLIC API - unchanged signature and return type from before.
    Runs the actual crawl in a separate child process (see _crawl_worker)
    so Playwright's sync API always gets a real main thread to work with,
    regardless of which thread called this function (e.g. FastAPI's
    background threadpool). Waits for the child process to finish and
    returns its result.
    """
    start_url = clean_url(start_url)

    ctx = multiprocessing.get_context("spawn")
    result_queue = ctx.Queue()
    process = ctx.Process(target=_crawl_worker, args=(start_url, max_pages, result_queue), daemon=True)
    process.start()

    # IMPORTANT: read from the queue BEFORE joining the process, not after.
    # multiprocessing.Queue on Windows is backed by a small OS pipe. If the
    # crawl results (HTML-derived data for several pages) are larger than
    # that pipe's buffer, the child blocks trying to write them while we
    # would be blocked in process.join() waiting for it to exit first -
    # both sides wait on each other forever (a classic deadlock). Reading
    # first drains the pipe so the child can finish writing and exit.
    try:
        status, payload, fully_crawled = result_queue.get(timeout=300)  # 5 min hard ceiling
    except Empty:
        process.terminate()
        process.join(timeout=5)
        return [_broken_page_entry(
            start_url,
            "The crawler process did not return any result within 5 minutes "
            "and was terminated. This usually means it crashed or hung.",
        )], True

    process.join(timeout=10)

    if status == "error":
        return [_broken_page_entry(start_url, f"Crawl failed: {payload}")], True

    return payload, fully_crawled