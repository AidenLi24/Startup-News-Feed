# Startup News Feed

A VC club dashboard that aggregates startup funding news from RSS feeds and uses Claude AI to extract and display recent funding rounds in a clean, dark-themed UI.

## What it does

- Pulls articles from startup/VC RSS feeds
- Filters for funding-related news
- Uses Claude Haiku to extract deal details (company, amount, round stage, investors, etc.)
- Displays deals in a live dashboard grouped by funding stage (Pre-Seed, Seed, Series A+)
- Caches results to disk so the page loads instantly without re-calling the API

## Requirements

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/AidenLi24/Startup-News-Feed.git
   cd Startup-News-Feed
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your API key**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

4. **Run the app**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

Hit the **Refresh** button in the UI to fetch the latest deals. Results are cached so subsequent loads are instant.
