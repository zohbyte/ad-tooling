#!/bin/env python
import os
import time
from datetime import datetime

import psycopg_pool
import requests

DELAY = 5
tick_length = int(os.getenv("TICK_LENGTH", 120 * 1000)) // 1000
start_date = os.getenv("TICK_START", "2018-06-27T13:00+02:00")
team_id = os.getenv("TEAM_ID", "1")
team_id_is_digit = team_id.isdigit()
team_id_int = int(team_id) if team_id_is_digit else None
flagid_endpoint = os.getenv("FLAGID_ENDPOINT", "https://glitch.ad/api/flagids")
flagid_scrape_enabled = os.getenv("FLAGID_SCRAPE", "") != ""
flagid_mode = os.getenv("FLAGID_MODE", "glitch" if "glitch" in flagid_endpoint else "team")

db = None
if flagid_scrape_enabled:
    print("STARTING FLAGIDS")
    print("CONFIG:")
    print("  DELAY:", DELAY)
    print("  TICK_LENGTH:", tick_length)
    print("  TICK_START:", start_date)
    print("  TIMESCALE:", os.environ.get("TIMESCALE"))
    print("  TEAM_ID:", team_id)
    print("  FLAGID_ENDPOINT:", flagid_endpoint)
    print("  FLAGID_MODE:", flagid_mode)
    db = psycopg_pool.ConnectionPool(os.environ["TIMESCALE"])
    print("CONNECTION TO TIMESCALE ESTABLISHED", flush=True)
else:
    print("FLAGID SCRAPE DISABLED", flush=True)


def extract_all_flagids(data):
    """Collect every flagid string from a nested Glitch scoreboard response."""
    if isinstance(data, dict):
        for value in data.values():
            yield from extract_all_flagids(value)
    elif isinstance(data, list):
        for item in data:
            yield from extract_all_flagids(item)
    elif isinstance(data, str):
        if data.strip():
            yield data.strip()
    elif isinstance(data, (int, float)):
        yield str(data)


def get_team_flagids(data):
    """Legacy mode: only flagids reachable under the configured team_id."""
    if isinstance(data, dict):
        if team_id in data:
            yield from extract_all_flagids(data[team_id])
        elif team_id_is_digit and team_id_int in data:
            yield from extract_all_flagids(data[team_id_int])
        else:
            for value in data.values():
                yield from get_team_flagids(value)
    elif isinstance(data, list):
        if team_id in data or (team_id_is_digit and team_id_int in data):
            yield
        else:
            for item in data:
                yield from get_team_flagids(item)
    elif isinstance(data, str):
        if data.strip():
            yield data.strip()


def parse_flagids(payload):
    if flagid_mode == "glitch":
        return list(dict.fromkeys(extract_all_flagids(payload)))
    return list(dict.fromkeys(get_team_flagids(payload)))


def update_flagids():
    assert db is not None

    response = requests.get(flagid_endpoint, timeout=15)
    response.raise_for_status()
    rows = [(node,) for node in parse_flagids(response.json()) if node]
    print("Updating flagids:", time.time(), f"({len(rows)})", flush=True)

    with db.connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO flag_id (content) VALUES (%s)", rows)
            conn.commit()


def main():
    start_datetime = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S%z")
    unixtime = time.mktime(start_datetime.timetuple())
    while True:
        try:
            if flagid_scrape_enabled:
                update_flagids()
            crnt_time = time.time()
            time_diff = max(0, crnt_time - unixtime)
            wait = (
                DELAY
                + tick_length * (time_diff // tick_length)
                + time_diff % tick_length
            )
            time.sleep(wait)
        except Exception as e:
            print("ERROR:", e, flush=True)
            time.sleep(10)


if __name__ == "__main__":
    main()
