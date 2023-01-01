# scrape

A proxy server for on-the-fly scraping of drug/trip/interaction data for Sojourn's future R&D.

### Setup instructions (dev)
---
1. Run from Terminal:

```bash
pipenv install
pipenv pipenv run uvicorn server:app --reload
```

2. Browse `http://localhost:8000/exp.php?ID=116897`. You should see an Erowid trip report in JSON format.
