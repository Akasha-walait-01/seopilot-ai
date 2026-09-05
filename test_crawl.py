from backend.tools.crawler import crawl_website

if __name__ == "__main__":
    results, full = crawl_website("https://books.toscrape.com", max_pages=4)
    print(len(results))
    print([r["url"] for r in results])