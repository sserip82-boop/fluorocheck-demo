from __future__ import annotations
from pathlib import Path
import csv
import json
import datetime


def save_csv(path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError('저장할 데이터가 없습니다.')
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def load_csv(path):
    with Path(path).open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
