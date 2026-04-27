import requests
from bs4 import BeautifulSoup


def crawl_news(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "lxml")

    title = _extract_title(soup)
    content = _extract_content(soup)
    image_url = _extract_image(soup)

    return {
        "title": title,
        "content": content,
        "image_url": image_url,
        "source_url": url
    }


def _extract_title(soup):
    selectors = [
        "h1.headline", "h1.title", "h2.title",
        'meta[property="og:title"]',
        "h1", "h2"
    ]
    for sel in selectors:
        tag = soup.select_one(sel)
        if tag:
            if tag.name == "meta":
                return tag.get("content", "").strip()
            if tag.get_text(strip=True):
                return tag.get_text(strip=True)
    return "제목 없음"


def _extract_content(soup):
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    selectors = [
        "article", "#articleBodyContents", "#articeBody",
        ".article-body", ".news-body", "#newsct_article",
        ".article_body", "div#content"
    ]
    for sel in selectors:
        tag = soup.select_one(sel)
        if tag:
            text = tag.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return text

    paragraphs = soup.find_all("p")
    text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)
    return text if text else "내용을 가져올 수 없습니다."


def _extract_image(soup):
    og_image = soup.select_one('meta[property="og:image"]')
    if og_image:
        return og_image.get("content", "")

    img = soup.select_one("article img, .article img, #articleBodyContents img")
    if img:
        return img.get("src", "")

    return ""
