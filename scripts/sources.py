# scripts/sources.py
from urllib.parse import quote_plus

def google_news_rss(query: str, hl="ko", gl="KR", ceid="KR:ko") -> str:
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

def sources_for_keyword(keyword: str) -> list[str]:
    return [
        google_news_rss(keyword),
    ]
