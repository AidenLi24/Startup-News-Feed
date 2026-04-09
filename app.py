#!/usr/bin/env python3
"""
Startup Deal Feed — VC Club Meeting Dashboard
Run: python app.py
Requires: ANTHROPIC_API_KEY environment variable
"""

import json
import os
import re
import time
from datetime import datetime, timezone, timedelta

import anthropic
import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Startup Deal Feed</title>
  <style>
    :root {
      --bg:       #0b0f1a;
      --surface:  #131929;
      --surface2: #1a2236;
      --border:   #263050;
      --text:     #e8edf5;
      --muted:    #7a8aaa;
      --accent:   #5b6ef5;

      --preseed-bg:  rgba(139, 92, 246, 0.15);
      --preseed-fg:  #b79eff;
      --seed-bg:     rgba(16, 185, 129, 0.15);
      --seed-fg:     #4ade9e;
      --seriesa-bg:  rgba(59, 130, 246, 0.15);
      --seriesa-fg:  #7ab8ff;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
      min-height: 100vh;
      line-height: 1.5;
    }

    /* ── Header ──────────────────────────────────────────────── */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
      gap: 1rem;
    }

    .logo { display: flex; align-items: center; gap: 0.75rem; }

    .logo-icon {
      width: 38px; height: 38px;
      background: linear-gradient(135deg, #5b6ef5, #8b5cf6);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px;
      flex-shrink: 0;
    }

    .logo-text h1 {
      font-size: 1.125rem;
      font-weight: 800;
      letter-spacing: -0.025em;
    }

    .logo-text .tagline {
      font-size: 0.7rem;
      color: var(--muted);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    #refresh-btn {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0.55rem 1.125rem;
      border-radius: 8px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.1s;
      white-space: nowrap;
      flex-shrink: 0;
    }
    #refresh-btn:hover  { opacity: 0.88; }
    #refresh-btn:active { transform: scale(0.96); }
    #refresh-btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

    /* ── Main ────────────────────────────────────────────────── */
    main {
      max-width: 1320px;
      margin: 0 auto;
      padding: 2rem 2rem 4rem;
    }

    /* ── Error banner ────────────────────────────────────────── */
    #error-banner {
      display: none;
      background: rgba(239,68,68,0.12);
      border: 1px solid rgba(239,68,68,0.35);
      color: #fca5a5;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      margin-bottom: 1.25rem;
      font-size: 0.875rem;
    }

    /* ── Controls bar ────────────────────────────────────────── */
    .controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }

    .filters { display: flex; gap: 0.5rem; flex-wrap: wrap; }

    .filter-btn {
      padding: 0.375rem 0.9rem;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--muted);
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s;
    }
    .filter-btn:hover { border-color: #445; color: var(--text); }
    .filter-btn.active { color: #fff; }

    .filter-btn[data-stage="All"].active      { background: var(--accent);  border-color: var(--accent); }
    .filter-btn[data-stage="Pre-Seed"].active { background: #7c3aed;         border-color: #7c3aed; }
    .filter-btn[data-stage="Seed"].active     { background: #059669;         border-color: #059669; }
    .filter-btn[data-stage="Series A"].active { background: #2563eb;         border-color: #2563eb; }

    .meta { font-size: 0.775rem; color: var(--muted); }

    /* ── Grid ────────────────────────────────────────────────── */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 1.125rem;
    }

    /* ── Card ────────────────────────────────────────────────── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.375rem;
      display: flex;
      flex-direction: column;
      gap: 0.875rem;
      transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
      animation: fadeUp 0.3s ease both;
    }
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(10px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .card:hover {
      border-color: #3a4f7a;
      transform: translateY(-3px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }

    .card-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 0.75rem;
    }

    .company-row { display: flex; align-items: center; gap: 0.6rem; }

    .logo-fallback {
      width: 28px; height: 28px;
      border-radius: 6px;
      background: linear-gradient(135deg, #5b6ef5, #8b5cf6);
      display: flex; align-items: center; justify-content: center;
      font-size: 0.75rem;
      font-weight: 800;
      color: #fff;
      flex-shrink: 0;
      border: 1px solid var(--border);
    }

    .company a {
      color: var(--text);
      text-decoration: none;
      border-bottom: 1px solid transparent;
      transition: border-color 0.15s, color 0.15s;
    }
    .company a:hover { color: #a5b4fc; border-bottom-color: #a5b4fc; }

    .company { font-size: 1.0625rem; font-weight: 800; letter-spacing: -0.02em; }

    .card-top-right {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 0.3rem;
      flex-shrink: 0;
    }

    .deal-date {
      font-size: 0.65rem;
      color: var(--muted);
      white-space: nowrap;
    }

    .badge {
      font-size: 0.65rem;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      padding: 0.22rem 0.65rem;
      border-radius: 999px;
      white-space: nowrap;
      flex-shrink: 0;
      margin-top: 2px;
    }
    .badge-Pre-Seed { background: var(--preseed-bg); color: var(--preseed-fg); }
    .badge-Seed     { background: var(--seed-bg);    color: var(--seed-fg); }
    .badge-Series-A { background: var(--seriesa-bg); color: var(--seriesa-fg); }

    .amount {
      font-size: 1.625rem;
      font-weight: 900;
      letter-spacing: -0.04em;
      line-height: 1;
    }

    .investors {
      font-size: 0.8rem;
      color: var(--muted);
    }
    .investors b { color: #9cb3d0; font-weight: 600; }

    .description {
      font-size: 0.8375rem;
      color: #b8c8de;
      line-height: 1.65;
    }

    .divider {
      border: none;
      border-top: 1px solid var(--border);
    }

    .talking-point {
      background: rgba(91, 110, 245, 0.09);
      border: 1px solid rgba(91, 110, 245, 0.22);
      border-radius: 10px;
      padding: 0.875rem;
    }
    .tp-label {
      font-size: 0.65rem;
      font-weight: 800;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: #8b9ef8;
      margin-bottom: 0.4rem;
    }
    .talking-point p {
      font-size: 0.8125rem;
      line-height: 1.7;
      color: #c4cff8;
    }

    .pros-cons {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.6rem;
    }

    .pros, .cons {
      border-radius: 8px;
      padding: 0.75rem;
    }

    .pros {
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .cons {
      background: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.2);
    }

    .pc-label {
      font-size: 0.62rem;
      font-weight: 800;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      margin-bottom: 0.45rem;
    }
    .pros .pc-label { color: #34d399; }
    .cons .pc-label { color: #f87171; }

    .pc-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }

    .pc-list li {
      font-size: 0.775rem;
      line-height: 1.45;
      display: flex;
      gap: 0.35rem;
    }

    .pros .pc-list li { color: #a7f3d0; }
    .cons .pc-list li { color: #fecaca; }

    .pros .pc-list li::before { content: '↑'; color: #34d399; flex-shrink: 0; }
    .cons .pc-list li::before { content: '↓'; color: #f87171; flex-shrink: 0; }

    /* ── Empty / loading states ──────────────────────────────── */
    .empty-state {
      grid-column: 1 / -1;
      text-align: center;
      padding: 5rem 2rem;
      color: var(--muted);
    }
    .empty-state .icon { font-size: 3rem; margin-bottom: 1rem; }
    .empty-state h2 { font-size: 1.1rem; margin-bottom: 0.5rem; color: var(--text); font-weight: 700; }
    .empty-state p  { font-size: 0.875rem; }

    .overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(11,15,26,0.82);
      backdrop-filter: blur(6px);
      z-index: 200;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: 1.25rem;
    }
    .overlay.show { display: flex; }

    .spinner {
      width: 44px; height: 44px;
      border: 3px solid var(--border);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.75s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    .overlay-msg {
      color: var(--muted);
      font-size: 0.9rem;
      letter-spacing: 0.01em;
    }


    .overlay-steps {
      display: flex;
      gap: 1.5rem;
      font-size: 0.75rem;
      color: #3d4f70;
    }
    .overlay-steps span.active { color: #8b9ef8; }

    /* ── Rotating icon ───────────────────────────────────────── */
    .rotate { display: inline-block; animation: spin 1s linear infinite; }
  </style>
</head>
<body>

<div class="overlay" id="overlay">
  <div class="spinner"></div>
  <p class="overlay-msg">Searching for recent funding announcements…</p>
  <div class="overlay-steps">
    <span id="step1" class="active">🔍 Searching web</span>
    <span id="step2">📊 Parsing deals</span>
    <span id="step3">✨ Building cards</span>
  </div>
</div>

<header>
  <div class="logo">
    <div class="logo-icon">📡</div>
    <div class="logo-text">
      <h1>Startup Deal Feed</h1>
      <div class="tagline">Seed · Series A</div>
    </div>
  </div>
  <button id="refresh-btn" onclick="doRefresh()">
    <span id="btn-icon">↺</span> Refresh Deals
  </button>
</header>

<main>
  <div id="error-banner"></div>

  <div class="controls">
    <div class="filters">
      <button class="filter-btn active" data-stage="All"      onclick="setFilter('All')">All Deals</button>
      <button class="filter-btn"        data-stage="Seed"     onclick="setFilter('Seed')">Seed</button>
      <button class="filter-btn"        data-stage="Series A" onclick="setFilter('Series A')">Series A</button>
    </div>
    <span class="meta" id="meta"></span>
  </div>

  <div class="grid" id="grid">
    <div class="empty-state">
      <div class="icon">📊</div>
      <h2>No deals loaded yet</h2>
      <p>Click <strong>Refresh Deals</strong> to fetch the latest funding announcements.</p>
    </div>
  </div>
</main>

<script>
  let allDeals = [];
  let activeFilter = 'All';
  let refreshController = null;
  let metaSuffix = '';

  // Step animation during load
  let stepTimer = null;
  function startSteps() {
    let s = 1;
    stepTimer = setInterval(() => {
      document.querySelectorAll('.overlay-steps span').forEach((el, i) => {
        el.classList.toggle('active', i + 1 === s);
      });
      s = s < 3 ? s + 1 : 2; // oscillate between 2-3 after initial
    }, 2200);
  }
  function stopSteps() {
    clearInterval(stepTimer);
    document.querySelectorAll('.overlay-steps span').forEach(el => el.classList.remove('active'));
  }

  function setFilter(stage) {
    activeFilter = stage;
    document.querySelectorAll('.filter-btn').forEach(btn =>
      btn.classList.toggle('active', btn.dataset.stage === stage)
    );
    renderCards();
  }

  function esc(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderCards() {
    const grid = document.getElementById('grid');
    const filtered = activeFilter === 'All'
      ? allDeals
      : allDeals.filter(d => d.stage === activeFilter);

    document.getElementById('meta').textContent =
      filtered.length + ' deal' + (filtered.length !== 1 ? 's' : '') + metaSuffix;

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <div class="icon">🔍</div>
          <h2>No ${activeFilter} deals found</h2>
          <p>Try a different stage filter or hit Refresh for new results.</p>
        </div>`;
      return;
    }

    grid.innerHTML = filtered.map((deal, i) => {
      const badgeClass = 'badge-' + deal.stage.replace(/\s+/g, '-');
      const investors = Array.isArray(deal.investors)
        ? deal.investors.join(', ')
        : (deal.investors || 'Undisclosed');

      const logoHtml = `<div class="logo-fallback">${esc(deal.company[0])}</div>`;

      const nameHtml = deal.website
        ? `<a href="${esc(deal.website)}" target="_blank" rel="noopener">${esc(deal.company)}</a>`
        : esc(deal.company);

      return `
      <div class="card" style="animation-delay:${i * 0.045}s">
        <div class="card-top">
          <div class="company">
            <div class="company-row">${logoHtml}<span>${nameHtml}</span></div>
          </div>
          <div class="card-top-right">
            <span class="badge ${badgeClass}">${esc(deal.stage)}</span>
            ${deal.date && deal.date !== 'Unknown' ? `<span class="deal-date">${esc(deal.date)}</span>` : ''}
          </div>
        </div>
        <div class="amount">${esc(deal.amount)}</div>
        <div class="investors"><b>Lead investors:</b> ${esc(investors)}</div>
        <div class="description">${esc(deal.description)}</div>
        <hr class="divider" />
        <div class="pros-cons">
          <div class="pros">
            <div class="pc-label">Pros</div>
            <ul class="pc-list">
              ${(deal.pros || []).map(p => `<li>${esc(p)}</li>`).join('')}
            </ul>
          </div>
          <div class="cons">
            <div class="pc-label">Cons</div>
            <ul class="pc-list">
              ${(deal.cons || []).map(c => `<li>${esc(c)}</li>`).join('')}
            </ul>
          </div>
        </div>
        <hr class="divider" />
        <div class="talking-point">
          <div class="tp-label">💬 Talking Point</div>
          <p>${esc(deal.talking_point)}</p>
        </div>
      </div>`;
    }).join('');
  }

  async function doRefresh() {
    const btn    = document.getElementById('refresh-btn');
    const icon   = document.getElementById('btn-icon');
    const overlay = document.getElementById('overlay');
    const errBanner = document.getElementById('error-banner');

    btn.disabled = true;
    icon.className = 'rotate';
    icon.textContent = '↺';
    overlay.classList.add('show');
    errBanner.style.display = 'none';
    startSteps();

    refreshController = new AbortController();

    try {
      const res  = await fetch('/api/refresh', { signal: refreshController.signal });
      const data = await res.json();

      if (data.error) {
        showError(data.error);
      } else {
        allDeals = data.deals || [];
        // Activate "Building cards" step briefly
        document.querySelectorAll('.overlay-steps span').forEach((el, i) =>
          el.classList.toggle('active', i === 2)
        );
        await new Promise(r => setTimeout(r, 400));
        const now = new Date();
        metaSuffix = ' · updated ' + now.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
          + ' · ' + (data.version || 'v0');
        renderCards();
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        showError('Network error: ' + err.message);
      }
    } finally {
      refreshController = null;
      btn.disabled = false;
      icon.className = '';
      icon.textContent = '↺';
      overlay.classList.remove('show');
      stopSteps();
    }
  }

  function showError(msg) {
    const b = document.getElementById('error-banner');
    b.textContent = '⚠ ' + msg;
    b.style.display = 'block';
  }

  // Auto-load cached deals on page open
  async function loadCached() {
    try {
      const res  = await fetch('/api/deals');
      const data = await res.json();
      if (data.deals && data.deals.length > 0) {
        allDeals = data.deals;
        if (data.fetched_at) {
          const d = new Date(data.fetched_at);
          metaSuffix = ' · last updated ' + d.toLocaleDateString([], {month:'short', day:'numeric'})
            + ' ' + d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
            + ' · ' + (data.version || 'v0');
        }
        renderCards();
      }
    } catch (_) {}
  }

  loadCached();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

EXTRACT_PROMPT = """\
You are a VC analyst. Below are multiple TechCrunch articles separated by "---ARTICLE---" markers.

For each article, determine if it is about a Seed or Series A funding round.
- Extract a JSON object only for Seed or Series A deals.
- Skip anything that is Pre-Seed, Series B or later, an acquisition, or not a funding announcement.

Return ONLY a valid JSON array of deal objects — no markdown fences, no explanation, nothing else.
If no articles qualify, return an empty array: []

Each deal object must have exactly these fields:
  "company"       — company name (string)
  "website"       — company homepage URL if explicitly mentioned in the article; otherwise null
  "stage"         — exactly one of: "Seed", "Series A"
  "amount"        — amount raised as a compact string e.g. "$4M" or "$25M" (use "Undisclosed" if unknown)
  "investors"     — array of lead investor / firm names (empty array if none mentioned)
  "description"   — one sentence describing what the company does
  "talking_point" — 2-3 sentences a VC club member could use to spark discussion about this deal
  "date"          — use the publication date provided in the article header exactly as given
  "pros"          — array of 2-3 short strings, investment strengths or tailwinds for this deal
  "cons"          — array of 2-3 short strings, risks or concerns about this deal
"""

RSS_FEEDS = [
    "https://techcrunch.com/category/venture/feed/",
    "https://news.crunchbase.com/venture/feed/",
    "https://news.crunchbase.com/startups/feed/",
    "https://www.finsmes.com/feed/",
    "https://feeds.feedburner.com/venturebeat/SZYF",
]

FUNDING_KEYWORDS = [
    "seed", "series a", "raises", "raised", "secures", "closes", "funding round",
]

ROUNDUP_KEYWORDS = [
    "week's", "biggest funding", "top funding", "funding rounds:",
    "funding surges", "funding in q", "funding to ",
    "snapshot:", "roundup", "record level", "this is a momentous",
    "not your imagination", "commanding higher valuations",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


def fetch_articles():
    """Pull articles from RSS feeds published in the last 7 days, deduplicated by URL."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    seen = set()
    articles = []
    for feed_url in RSS_FEEDS:
        feed_count = 0
        try:
            resp = requests.get(feed_url, timeout=6, headers=HEADERS)
            feed = feedparser.parse(resp.text)
        except Exception as e:
            print(f"  [FEED ERROR] {feed_url} — {e}")
            continue
        for entry in feed.entries:
            url = entry.get("link", "")
            if not url or url in seen:
                continue

            # Parse publish date and skip articles older than 7 days
            published_parsed = entry.get("published_parsed")
            if published_parsed:
                pub_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue
                pub_str = pub_dt.strftime("%b %-d, %Y")
            else:
                pub_str = "Unknown"

            seen.add(url)
            feed_count += 1
            raw_summary = entry.get("summary", "")
            summary = BeautifulSoup(raw_summary, "html.parser").get_text(separator=" ", strip=True)
            articles.append({
                "url": url,
                "title": entry.get("title", ""),
                "summary": summary,
                "date": pub_str,
            })
        print(f"  [FEED] {feed_url.split('/')[2]} → {feed_count} recent articles")
    return articles


def looks_like_funding(article):
    title_lower = article["title"].lower()
    # Skip roundup/digest/analysis articles
    if any(kw in title_lower for kw in ROUNDUP_KEYWORDS):
        return False
    text = (title_lower + " " + article["summary"].lower())
    return any(kw in text for kw in FUNDING_KEYWORDS)


def fetch_article_text(url, fallback_summary=""):
    """Fetch a page and return article body text, falling back to RSS summary."""
    try:
        resp = requests.get(url, timeout=5, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try TechCrunch-specific article body selectors first
        body = None
        for selector in [
            {"class": "article-content"},
            {"class": "entry-content"},
            {"itemprop": "articleBody"},
            {"class": "post-content"},
        ]:
            container = soup.find(attrs=selector)
            if container:
                paragraphs = container.find_all("p")[:20]
                body = "\n".join(p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(strip=True))
                if body:
                    break

        # Generic fallback: all <p> tags
        if not body:
            paragraphs = soup.find_all("p")[:20]
            body = "\n".join(p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(strip=True))

        return body if body else fallback_summary
    except Exception:
        return fallback_summary


VERSION = "v11"

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache.json")


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"deals": [], "fetched_at": None}


def save_cache(deals):
    from datetime import datetime
    with open(CACHE_FILE, "w") as f:
        json.dump({"deals": deals, "fetched_at": datetime.now().isoformat()}, f)


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/deals")
def api_deals():
    """Return cached deals — no API call, instant load."""
    data = load_cache()
    data["version"] = VERSION
    return jsonify(data)


@app.route("/api/refresh")
def api_refresh():
    try:
        return _do_refresh()
    except Exception as exc:
        return jsonify({"deals": [], "error": f"Unexpected error: {exc}"})


def _do_refresh():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({
            "deals": [],
            "error": (
                "ANTHROPIC_API_KEY is not set. "
                "Export it in your shell: export ANTHROPIC_API_KEY=sk-..."
            ),
        })

    client = anthropic.Anthropic(api_key=api_key)

    # 1. Pull RSS feeds and filter to funding-related articles
    articles = fetch_articles()
    candidates = [a for a in articles if looks_like_funding(a)][:20]
    print(f"  [FILTER] {len(articles)} total recent articles → {len(candidates)} funding candidates")
    for c in candidates:
        print(f"    · {c['title'][:80]}")

    if not candidates:
        return jsonify({"deals": [], "error": "No funding articles found in feeds. Try again later."})

    # 2. Fetch full text for all candidates (RSS summary used as fallback)
    article_blocks = []
    for article in candidates:
        body = fetch_article_text(article["url"], fallback_summary=article["summary"])
        if body:
            article_blocks.append(f"Title: {article['title']}\nPublished: {article['date']}\n\n{body}")

    if not article_blocks:
        return jsonify({"deals": [], "error": "Could not fetch article content. Try refreshing."})

    # 3. Single batched Haiku call with all articles combined
    combined = "\n\n---ARTICLE---\n\n".join(article_blocks)
    prompt = f"{EXTRACT_PROMPT}\n\nArticles:\n\n---ARTICLE---\n\n{combined}"

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        return jsonify({"deals": [], "error": f"Anthropic API error: {e}"})

    raw = response.content[0].text.strip()

    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        return jsonify({"deals": [], "error": "Could not parse deals from response. Try refreshing."})

    try:
        deals = json.loads(match.group())
    except json.JSONDecodeError as exc:
        return jsonify({"deals": [], "error": f"JSON parse error: {exc}"})

    print(f"  [MODEL] returned {len(deals)} deals")
    if not deals:
        return jsonify({"deals": [], "error": "No qualifying funding rounds found. Try refreshing."})

    save_cache(deals)
    return jsonify({"deals": deals, "fetched_at": None, "version": VERSION, "error": None})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  Startup Deal Feed → http://localhost:{port}\n")
    app.run(host="127.0.0.1", debug=False, port=port)
