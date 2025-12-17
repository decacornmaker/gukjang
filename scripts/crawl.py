# scripts/crawl.py
import json, os, re, hashlib
from datetime import datetime, timezone
from dateutil import parser as dtparser
import feedparser

from sources import sources_for_keyword

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
BY_DATE_DIR = os.path.join(DATA_DIR, "by-date")
BY_KW_DIR = os.path.join(DATA_DIR, "by-keyword")

ITEMS_PATH = os.path.join(DATA_DIR, "items.json")

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BY_DATE_DIR, exist_ok=True)
    os.makedirs(BY_KW_DIR, exist_ok=True)

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def normalize_url(url: str) -> str:
    # 구글뉴스 RSS는 리다이렉트/추적 파라미터가 붙는 경우가 있어 최소 정규화만
    url = url.strip()
    url = re.sub(r"[#?].*$", "", url)  # MVP: query/fragment 제거
    return url

def item_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

def parse_published(entry) -> str:
    # RSS마다 published/updated가 다름
    dt = None
    if getattr(entry, "published", None):
        dt = dtparser.parse(entry.published)
    elif getattr(entry, "updated", None):
        dt = dtparser.parse(entry.updated)
    else:
        dt = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()

def iso_to_date(iso: str) -> str:
    dt = dtparser.parse(iso)
    return dt.date().isoformat()

def read_keywords():
    path = os.path.join(ROOT, "keywords.txt")
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def main():
    ensure_dirs()

    all_items = load_json(ITEMS_PATH, [])
    by_id = {it["id"]: it for it in all_items}

    existing_urls = set(normalize_url(it["url"]) for it in all_items if "url" in it)

    keywords = read_keywords()
    new_count = 0

    for kw in keywords:
        for feed_url in sources_for_keyword(kw):
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:50]:
                url = normalize_url(getattr(entry, "link", "") or "")
                if not url:
                    continue
                if url in existing_urls:
                    continue

                title = (getattr(entry, "title", "") or "").strip()
                source = ""
                if getattr(entry, "source", None) and getattr(entry.source, "title", None):
                    source = entry.source.title.strip()

                published = parse_published(entry)
                snippet = ""
                if getattr(entry, "summary", None):
                    snippet = re.sub(r"<[^>]+>", "", entry.summary).strip()
                    snippet = re.sub(r"\s+", " ", snippet)[:240]

                _id = item_id(url)
                item = {
                    "id": _id,
                    "keyword": kw,
                    "title": title,
                    "url": url,
                    "source": source,
                    "publishedAt": published,   # UTC ISO
                    "date": iso_to_date(published),
                    "snippet": snippet,
                    "collectedAt": datetime.now(timezone.utc).isoformat(),
                }

                by_id[_id] = item
                existing_urls.add(url)
                new_count += 1

    # 최신순 정렬
    merged = list(by_id.values())
    merged.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)

    save_json(ITEMS_PATH, merged)

    # 날짜별/키워드별 파일 생성(가볍게 최근 N개)
    # 너무 커지는 것 방지: 전체는 items.json, 분류 파일은 최근 1000개 정도만
    recent = merged[:1000]

    by_date = {}
    by_kw = {}
    for it in recent:
        by_date.setdefault(it["date"], []).append(it)
        by_kw.setdefault(it["keyword"], []).append(it)

    for d, items in by_date.items():
        save_json(os.path.join(BY_DATE_DIR, f"{d}.json"), items)

    # 키워드 파일명 안전하게
    def safe_kw(s: str) -> str:
        return re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", s).strip("_")[:60] or "kw"

    for k, items in by_kw.items():
        save_json(os.path.join(BY_KW_DIR, f"{safe_kw(k)}.json"), items)

    print(f"✅ done. new items: {new_count}, total: {len(merged)}")

if __name__ == "__main__":
    main()
