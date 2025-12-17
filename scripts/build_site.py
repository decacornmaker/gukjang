# scripts/build_site.py
import json, os, re
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT, "data", "items.json")
PUBLIC_DIR = os.path.join(ROOT, "public")
K_DIR = os.path.join(PUBLIC_DIR, "k")

def load_items():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def read_keywords():
    path = os.path.join(ROOT, "keywords.txt")
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def safe_kw(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", s).strip("_")[:60] or "kw"

def html_escape(s: str) -> str:
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def render_page(title, body, desc="키워드 뉴스 아카이브"):
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html_escape(title)}</title>
  <meta name="description" content="{html_escape(desc)}" />
  <link rel="stylesheet" href="/style.css" />
</head>
<body>
  <header class="top">
    <div class="wrap">
      <a class="brand" href="/">키워드 뉴스 아카이브</a>
    </div>
  </header>
  <main class="wrap">
    {body}
  </main>
  <footer class="wrap foot">
    <p>Updated: {datetime.utcnow().isoformat()}Z</p>
  </footer>
</body>
</html>
"""

def build():
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    os.makedirs(K_DIR, exist_ok=True)

    items = load_items()
    kws = read_keywords()

    # 인덱스(최신)
    latest = items[:80]
    latest_list = "\n".join(
        f"""<li class="item">
  <a href="{html_escape(it["url"])}" target="_blank" rel="noopener">
    <div class="t">{html_escape(it["title"])}</div>
  </a>
  <div class="m">
    <span class="k"><a href="/k/{safe_kw(it["keyword"])}.html">#{html_escape(it["keyword"])}</a></span>
    <span class="s">{html_escape(it.get("source",""))}</span>
    <span class="d">{html_escape(it.get("date",""))}</span>
  </div>
  <div class="sn">{html_escape(it.get("snippet",""))}</div>
</li>"""
        for it in latest
    )

    kw_links = " ".join(
        f'<a class="pill" href="/k/{safe_kw(k)}.html">#{html_escape(k)}</a>'
        for k in kws
    )

    index_body = f"""
<h1>최신 뉴스</h1>
<div class="pills">{kw_links}</div>
<ul class="list">{latest_list}</ul>
"""
    with open(os.path.join(PUBLIC_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_page("키워드 뉴스 아카이브", index_body))

    # 키워드별 페이지
    for k in kws:
        k_items = [it for it in items if it["keyword"] == k][:200]
        li = "\n".join(
            f"""<li class="item">
  <a href="{html_escape(it["url"])}" target="_blank" rel="noopener">
    <div class="t">{html_escape(it["title"])}</div>
  </a>
  <div class="m">
    <span class="s">{html_escape(it.get("source",""))}</span>
    <span class="d">{html_escape(it.get("date",""))}</span>
  </div>
  <div class="sn">{html_escape(it.get("snippet",""))}</div>
</li>"""
            for it in k_items
        )
        body = f"""
<h1>#{html_escape(k)}</h1>
<div class="pills"><a class="pill" href="/">← 최신으로</a></div>
<ul class="list">{li}</ul>
"""
        filename = os.path.join(K_DIR, f"{safe_kw(k)}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(render_page(f"#{k} - 키워드 뉴스 아카이브", body, desc=f"{k} 관련 뉴스 아카이브"))

    print("✅ site built")

if __name__ == "__main__":
    build()
