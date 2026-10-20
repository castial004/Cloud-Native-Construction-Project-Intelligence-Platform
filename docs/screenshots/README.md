# Dashboard Screenshots

These are real captures of the running platform, embedded in
`project-final.pptx`.

## Pages captured
| File | Page | URL |
|------|------|-----|
| 01-overview.png   | Executive Overview | `/` |
| 02-cost.png       | Cost Performance   | `/cost` |
| 03-schedule.png   | Schedule Performance | `/schedule` |
| 04-risk.png       | Delay-Risk View    | `/risk` |
| 05-activities.png | Activity Explorer  | `/activities` |
| 06-data.png       | Data & Actions     | `/data` |

## Regenerate
```bash
# 1. start the platform
platform/run.sh

# 2. capture (headless Chrome)
cd platform
mkdir -p ../docs/screenshots
shoot() {
  google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size=1600,1000 --force-device-scale-factor=1.5 \
    --virtual-time-budget=8000 --screenshot="$2" "$1" >/dev/null 2>&1
}
shoot "http://localhost:8080/"           "../docs/screenshots/01-overview.png"
shoot "http://localhost:8080/cost"       "../docs/screenshots/02-cost.png"
shoot "http://localhost:8080/schedule"   "../docs/screenshots/03-schedule.png"
shoot "http://localhost:8080/risk"       "../docs/screenshots/04-risk.png"
shoot "http://localhost:8080/activities" "../docs/screenshots/05-activities.png"
shoot "http://localhost:8080/data"       "../docs/screenshots/06-data.png"

# 3. rebuild the deck
platform/.venv/bin/python build_deck.py
```
