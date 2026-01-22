#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 15:23:57 2026

@author: richardfeng
"""

# storage/counter_store.py
import json
from pathlib import Path


class CounterStore:
    """
    Persistent counters for:
    - Transaction ID (TX1001, TX1002, ...)
    - Voucher code  (V0000001, V0000002, ...)

    Stored in counters.json to survive server restarts.
    """

    def __init__(self, counter_file_path: Path):
        self.counter_file_path = counter_file_path
        self._ensure_file()

    def _ensure_file(self) -> None:
        if self.counter_file_path.exists():
            return
        self.counter_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.counter_file_path.write_text(
            json.dumps({"tx": 1000, "v": 0}, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> dict:
        try:
            raw = self.counter_file_path.read_text(encoding="utf-8").strip()
            if not raw:
                return {"tx": 1000, "v": 0}
            return json.loads(raw)
        except Exception:
            return {"tx": 1000, "v": 0}

    def _save(self, data: dict) -> None:
        self.counter_file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def next_transaction_id(self) -> str:
        data = self._load()
        data["tx"] = int(data.get("tx", 1000)) + 1
        self._save(data)
        return f"TX{data['tx']}"

    def next_voucher_code(self) -> str:
        data = self._load()
        data["v"] = int(data.get("v", 0)) + 1
        self._save(data)
        return f"V{data['v']:07d}"