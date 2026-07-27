# SciBot Platform

A self-contained web app for uploading scientific PDFs and running Claude-powered
**classify**, **summarize**, and **pairwise-rank** bots against them — no MySQL,
GROBID, or GPU libraries required.

This is a simplified rebuild of the uploaded `SciBot` toolkit (originally built for a
research-lab setup with MySQL + GROBID XML parsing + CLIP image embeddings). It keeps
the same core bot logic and prompts, but:
- Uses **SQLite** instead of MySQL (single file, zero setup)
- Extracts PDF text directly with `pypdf` instead of GROBID
- Skips image/figure embedding (CLIP/torch) — text-only for now
- Ports the LLM calls to the current Anthropic Messages API (the original code used a
  deprecated `client.completion()` style that no longer works)

## 1. Install

Requires Python 3.9+.

```bash
cd scibot_platform
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Add your Anthropic API key

Get a key from https://console.anthropic.com/ (Settings → API Keys).

**Option A — environment variable (recommended):**
```bash
export ANTHROPIC_API_KEY="sk-ant-...your-key..."
```

**Option B — config file:**
```bash
cp config.example.json config.json
# then edit config.json and paste your key in
```

Never commit `config.json` with a real key to git — it's already covered by a
reasonable `.gitignore` pattern (`config.json`) if you set one up.

## 3. Run it

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser (on your computer, or from your phone
if it's on the same Wi-Fi — see below).

## 4. Using it from your phone

This app runs on whatever computer you start it on — it doesn't run natively on
Android. To reach it from your phone:
- Make sure your phone and computer are on the same Wi-Fi network
- Find your computer's local IP (e.g. `192.168.1.42`) — on Mac/Linux: `ifconfig`, on
  Windows: `ipconfig`
- Change the last line of `app.py` to `app.run(debug=True, host="0.0.0.0", port=5000)`
- On your phone's browser, go to `http://192.168.1.42:5000`

For access from anywhere (not just home Wi-Fi), you'd deploy this to a small cloud
server (e.g. a $5/month VPS, Render, Railway, or Fly.io) — happy to help with that
step whenever you're ready.

## What each page does

- **Library** (`/`) — upload one or more PDFs; each becomes a document record with
  extracted text
- **Document detail** (`/document/<id>`) — run Classify or Summarize on that document,
  see the text preview
- **Rank** (`/compare`) — pick two documents, Claude judges which is more likely to be
  high-impact; running more comparisons builds up a win/loss standings table

## Known limitations (vs. the original lab toolkit)

- No author/title metadata extraction — title is a rough guess from the first
  reasonable line of text. You can improve this later with a proper metadata parser.
- No image/figure similarity search (the original `ImageBot`/CLIP feature).
- No multi-turn chat/answer-bot with retrieval — this focuses on the three core
  document-level tools you asked for.
- Single-user, local-only by default. Fine for personal use; would need auth and a
  production server (gunicorn, etc.) before sharing with others.

## File map

```
app.py            Flask routes / app entry point
db.py             SQLite storage (documents, classifications, summaries, rankings)
llm_bots.py       Classify/Compare/Summarize bot logic (ported from your tool_bots.py)
pdf_utils.py      PDF → plain text extraction
config.py         Loads API key from env var or config.json
templates/        HTML pages
static/style.css  Styling
uploads/          Saved PDF files (created automatically)
data/scibot.db    SQLite database (created automatically)
```
