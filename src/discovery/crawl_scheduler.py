import json
import os
import time

DATA_PATH = "data/greenhouse_schedule.json"
DEFAULT_INTERVAL = 6 * 3600   # 6 hours

def load_schedule():
    if not os.path.exists(DATA_PATH):
        return {}
    try:
        with open(DATA_PATH) as f:
            return json.load(f)
    except:
        return {}

def save_schedule(schedule):
    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(schedule, f, indent=2)

def should_scrape(company, schedule):
    last = schedule.get(company)
    if not last:
        return True
    return (time.time() - last) > DEFAULT_INTERVAL

def mark_scraped(company, schedule):
    schedule[company] = int(time.time())