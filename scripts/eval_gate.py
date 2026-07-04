#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def predict(signals: int, irreversible: bool, mechanical: bool) -> str:
    if mechanical:
        return 'L0'
    if irreversible and signals >= 1:
        return 'escalate'
    if signals >= 2:
        return 'escalate'
    return 'L0'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('cases', nargs='?', default=str(Path(__file__).resolve().parents[1] / 'benchmarks' / 'gate_cases.jsonl'))
    args = ap.parse_args()
    total = ok = 0
    for line in Path(args.cases).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        pred = predict(int(row.get('signals', 0)), bool(row.get('irreversible')), bool(row.get('mechanical')))
        expected = row.get('expected')
        total += 1
        ok += int(pred == expected)
        print(f"{row.get('id')}: pred={pred} expected={expected} {'OK' if pred == expected else 'FAIL'}")
    print(f'Accuracy: {ok}/{total}')
    return 0 if ok == total else 1

if __name__ == '__main__':
    raise SystemExit(main())
