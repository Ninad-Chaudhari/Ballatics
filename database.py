import re
import json
from datetime import datetime, timezone, timedelta
import os
import requests
from flask import Flask, jsonify, render_template, request, abort
from apscheduler.schedulers.background import BackgroundScheduler

from sqlalchemy import (
    create_engine, Column, Integer, Float, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker

import logging
logging.basicConfig(level=logging.INFO)

# ─── Configuration ─────────────────────────────────────────────────────────────
TOTAL_BALLOONS = 1000
WIND_API_BASE  = "https://a.windbornesystems.com/treasure"
POINT_RE       = re.compile(r'\[\s*[-\d.eE]+,\s*[-\d.eE]+,\s*[-\d.eE]+\s*\]')

# ─── Database Setup ────────────────────────────────────────────────────────────
engine = create_engine('sqlite:///balloons.db', echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class BalloonData(Base):
    __tablename__ = 'balloon_data'
    id            = Column(Integer, primary_key=True)
    balloon_index = Column(Integer, nullable=False)
    timestamp     = Column(DateTime(timezone=True), nullable=False, index=True)
    lat           = Column(Float, nullable=True)
    lon           = Column(Float, nullable=True)
    alt           = Column(Float, nullable=True)

Base.metadata.create_all(engine)

# ─── Fetch & Insert Logic ─────────────────────────────────────────────────────
def fetch_and_update():
    print(f"[{datetime.now()}] fetch_and_update() was called.")
    logging.info(f"[{datetime.now()}] fetch_and_update() was called.")
    session = SessionLocal()
    now = datetime.now(timezone.utc)
    end_ts = now.replace(minute=0, second=0, microsecond=0)

    # determine next timestamp to fetch
    last_ts = session.query(func.max(BalloonData.timestamp)).scalar()
    print(f"Last timestamp called:{last_ts}")
    print(f"Current timestamp :{end_ts}")
    logging.info(f"Last timestamp called:{last_ts}")
    logging.info(f"Current timestamp :{end_ts}")
    if last_ts:
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)
        next_ts = last_ts + timedelta(hours=1)
    else:
        # backfill past 24h
        next_ts = end_ts - timedelta(hours=23)

    ts = next_ts
    while ts <= end_ts:
        offset = int((now - ts).total_seconds() // 3600)
        url    = f"{WIND_API_BASE}/{offset:02d}.json"

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            blocks = POINT_RE.findall(r.text)

            pts = []
            for b in blocks:
                try:
                    arr = json.loads(b)
                    if isinstance(arr, list) and len(arr) >= 2:
                        pts.append(arr)
                except json.JSONDecodeError:
                    continue

            # trim or pad to TOTAL_BALLOONS
            if len(pts) > TOTAL_BALLOONS:
                pts = pts[:TOTAL_BALLOONS]

            # insert data rows
            for i in range(TOTAL_BALLOONS):
                if i < len(pts):
                    lat, lon = pts[i][0], pts[i][1]
                    alt      = pts[i][2] if len(pts[i]) > 2 else None
                else:
                    lat = lon = alt = None

                session.add(BalloonData(
                    balloon_index=i,
                    timestamp=ts,
                    lat=lat,
                    lon=lon,
                    alt=alt
                ))

            session.commit()
            print(f"[{datetime.now(timezone.utc)}] inserted {len(pts)} points (+ {TOTAL_BALLOONS-len(pts)} NULLs) for {ts.isoformat()}")

        except Exception as e:
            print(f"[{datetime.now(timezone.utc)}] ERROR fetching {url}: {e}")
            # on error, insert TOTAL_BALLOONS NULL rows
            for i in range(TOTAL_BALLOONS):
                session.add(BalloonData(
                    balloon_index=i,
                    timestamp=ts,
                    lat=None,
                    lon=None,
                    alt=None
                ))
            session.commit()
            print(f"[{datetime.now(timezone.utc)}] inserted {TOTAL_BALLOONS} NULLs for {ts.isoformat()}")

        ts += timedelta(hours=1)

    session.close()

# ─── Flask + Scheduler Setup ───────────────────────────────────────────────────
app = Flask(__name__)


# schedule job every hour on the hour
from sqlalchemy import func
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_update, 'cron', id='updateDatabase', second=20)

@app.route("/trajectory/<int:balloon_id>")
def get_trajectory(balloon_id):
    session = SessionLocal()
    recs = (
        session.query(BalloonData)
        .filter_by(balloon_index=balloon_id)
        .order_by(BalloonData.timestamp)
        .all()
    )
    traj = [
        {"timestamp": r.timestamp.isoformat(), "lat": r.lat, "lon": r.lon, "alt": r.alt}
        for r in recs
    ]
    session.close()
    return jsonify({"balloon_index": balloon_id, "trajectory": traj})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run_fetch", methods=["POST", "GET"])
def run_fetch():
    fetch_and_update()
    return "OK", 200


@app.route("/health_check")
def health_check():
    return "App Deployed Successfully"

if __name__ == "__main__":
    fetch_and_update()   # initial backfill/update

    # Start scheduler AFTER fetch
    scheduler.start()
    print("Scheduled jobs:", scheduler.get_jobs())

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
