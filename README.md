# Linkup Morning Report — EdTech India

A real-time morning intelligence report for EdTech founders in India, powered by the [Linkup API](https://linkup.so).

## What it does

Fetches live data across four dimensions and synthesizes it into an actionable report:

1. **EdTech Funding & Startups** — latest investments, Series A/B rounds, acquisitions
2. **Student Behavior & Trends** — how Indian learners engage with education in 2026
3. **Government Policy & Regulation** — NEP updates, regulatory changes
4. **AI in Education** — AI tutoring, personalized learning breakthroughs

## Web App

Open `index.html` in a browser. No build step needed.

- Enter your Linkup API key
- Choose search depth (Fast / Standard / Deep)
- Add or remove queries
- Click **Generate Report** for a formatted, dark-themed report
- Copy as text or print

### Deploy

**Vercel:**
```bash
vercel
```

**Railway / Docker:**
```bash
docker build -t linkup-report .
docker run -p 8080:8080 -e PORT=8080 linkup-report
```

## CLI

```bash
pip install -r requirements.txt
export LINKUP_API_KEY=your_key_here
python report.py
```

### CLI Options

```
--depth {fast,standard,deep}   Search depth (default: deep)
--timeout SECONDS              Request timeout (default: 60)
--parallel                     Run queries in parallel
--export-json FILE             Export report as JSON
--query "custom query"         Add custom queries (repeatable)
```

### Examples

```bash
# Fast parallel run
python report.py --depth fast --parallel

# Add custom queries
python report.py --query "edtech IPO India 2026" --query "vernacular learning apps India"

# Export to JSON
python report.py --export-json report.json
```

## Requirements

- Python 3.10+ (CLI)
- A [Linkup API](https://linkup.so) key
