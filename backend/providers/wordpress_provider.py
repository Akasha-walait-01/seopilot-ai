# This file is our WordPress CMS integration layer.
# Uses the standard WordPress REST API with Application Passwords for auth.
# IMPORTANT HONESTY NOTE (spec rule: never fabricate results):
# - Title and Content are natively supported by the WordPress REST API.
# - Meta Description is only written via the Yoast SEO plugin's registered
#   meta field. If the site does not use Yoast, WordPress may ignore this
#   part silently - we always tell the user this clearly, we never claim
#   success without checking the actual WordPress response.
# - H1 has no dedicated field in WordPress (it depends on the theme), so
#   this provider does NOT attempt to auto-apply an H1 change. It is
#   returned as a manual recommendation instead.
# Note: the Application Password is stored as-is in the local SQLite
# database for this project - it is not encrypted. Fine for local/dev use,
# not recommended for a production deployment without extra hardening.

import base64
import json as json_lib
from urllib.parse import urlparse

import requests


class WordPressProvider:
    def __init__(self, site_url: str, username: str, app_password: str):
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password

    def _headers(self) -> dict:
        token = base64.b64encode(f"{self.username}:{self.app_password}".encode()).decode()
        return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    def test_connection(self) -> dict:
        """
        Checks if the given site URL + credentials actually work, by asking
        WordPress who the authenticated user is. Never assumes success.
        """
        try:
            resp = requests.get(
                f"{self.site_url}/wp-json/wp/v2/users/me",
                headers=self._headers(), timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "connected": True,
                    "message": f"Connected successfully as '{data.get('name', self.username)}'.",
                    "site_name": data.get("name"),
                }
            elif resp.status_code == 401:
                return {
                    "connected": False,
                    "message": "Authentication failed. Check the site URL, username, and Application Password.",
                    "site_name": None,
                }
            else:
                return {
                    "connected": False,
                    "message": f"Unexpected response from WordPress ({resp.status_code}): {resp.text[:200]}",
                    "site_name": None,
                }
        except requests.exceptions.RequestException as e:
            return {"connected": False, "message": f"Could not reach the WordPress site: {e}", "site_name": None}

    def find_post_or_page_by_url(self, page_url: str) -> dict | None:
        """
        Looks up a WordPress post OR page by matching the URL slug.
        Returns None if nothing matches - never guesses a post ID.
        """
        path = urlparse(page_url).path.strip("/")
        slug = path.split("/")[-1] if path else ""
        if not slug:
            return None

        try:
            resp = requests.get(
                f"{self.site_url}/wp-json/wp/v2/posts",
                params={"slug": slug}, headers=self._headers(), timeout=15,
            )
            if resp.status_code == 200 and resp.json():
                return resp.json()[0]

            resp_pages = requests.get(
                f"{self.site_url}/wp-json/wp/v2/pages",
                params={"slug": slug}, headers=self._headers(), timeout=15,
            )
            if resp_pages.status_code == 200 and resp_pages.json():
                return resp_pages.json()[0]

            return None
        except requests.exceptions.RequestException:
            return None

    def create_draft_post(self, title: str, content_html: str, excerpt: str | None = None) -> dict:
        """
        Creates a new WordPress post with status=draft. Never publishes
        directly - the human publishes manually from the WordPress admin.
        """
        payload = {"title": title, "content": content_html, "status": "draft"}
        if excerpt:
            payload["excerpt"] = excerpt

        try:
            resp = requests.post(
                f"{self.site_url}/wp-json/wp/v2/posts",
                json=payload, headers=self._headers(), timeout=30,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "success": True,
                    "post_id": data.get("id"),
                    "edit_link": data.get("link"),
                    "message": "Draft created successfully in WordPress. Please review and publish it manually.",
                }
            else:
                return {
                    "success": False, "post_id": None, "edit_link": None,
                    "message": f"WordPress rejected the request ({resp.status_code}): {resp.text[:300]}",
                }
        except requests.exceptions.RequestException as e:
            return {"success": False, "post_id": None, "edit_link": None, "message": f"Could not reach the WordPress site: {e}"}

    def inject_schema_into_post(self, post_id: int, schema_blocks: list[dict]) -> dict:
        """
        Appends JSON-LD <script> tags for the given schema blocks to the
        end of the post's existing content. Fetches the current content
        first so nothing already there is lost.
        """
        try:
            get_resp = requests.get(
                f"{self.site_url}/wp-json/wp/v2/posts/{post_id}",
                headers=self._headers(), timeout=15,
            )
            if get_resp.status_code != 200:
                return {"success": False, "message": f"Could not fetch the existing post ({get_resp.status_code})."}

            current = get_resp.json()
            current_content = current.get("content", {}).get("raw") or current.get("content", {}).get("rendered", "")

            script_tags = ""
            for block in schema_blocks:
                script_tags += f'\n<script type="application/ld+json">{json_lib.dumps(block)}</script>\n'

            update_resp = requests.post(
                f"{self.site_url}/wp-json/wp/v2/posts/{post_id}",
                json={"content": current_content + script_tags},
                headers=self._headers(), timeout=30,
            )
            if update_resp.status_code == 200:
                return {"success": True, "message": "Schema markup injected into the post content."}
            else:
                return {"success": False, "message": f"WordPress rejected the update ({update_resp.status_code}): {update_resp.text[:300]}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Could not reach the WordPress site: {e}"}

    def update_post_title_and_meta_description(self, post_id: int, title: str | None, meta_description: str | None) -> dict:
        """
        Updates the post title (native WordPress field) and attempts to
        update the Yoast SEO meta description field. If the site does not
        use Yoast, WordPress will typically ignore the meta field silently -
        this is disclosed to the user in the returned message, never hidden.
        """
        payload = {}
        if title:
            payload["title"] = title
        if meta_description:
            payload["meta"] = {"_yoast_wpseo_metadesc": meta_description}

        if not payload:
            return {"success": False, "message": "Nothing to update."}

        try:
            resp = requests.post(
                f"{self.site_url}/wp-json/wp/v2/posts/{post_id}",
                json=payload, headers=self._headers(), timeout=30,
            )
            if resp.status_code == 200:
                note = ""
                if meta_description:
                    note = (
                        " Note: the meta description update only takes effect if the Yoast SEO "
                        "plugin is active on this site and exposes its fields to the REST API. "
                        "If the site uses a different SEO plugin or none at all, WordPress may "
                        "have silently ignored that part - please verify on the site."
                    )
                return {"success": True, "message": f"Post updated successfully.{note}"}
            else:
                return {"success": False, "message": f"WordPress rejected the update ({resp.status_code}): {resp.text[:300]}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Could not reach the WordPress site: {e}"}