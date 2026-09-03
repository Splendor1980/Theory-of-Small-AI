"""Hebbian-ассоциативная память (градиент-фри обучение).

Усиливает связи между сущностями при совместной активации,
затухает со временем. По мотивам Hillock/пластичности.
"""
from collections import defaultdict
import sqlite3
import json


class HebbianMemory:
    def __init__(self, db_path="hebbian.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS weights (
                a TEXT NOT NULL,
                b TEXT NOT NULL,
                w REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (a, b)
            )
        """)
        self.conn.commit()
        self.eta = 0.15
        self.decay = 0.01

    def coactivate(self, entities):
        """Усиливаем связи между всеми парами активных сущностей."""
        ents = sorted(set(e.lower().strip() for e in entities if e))
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                a, b = ents[i], ents[j]
                key_pair = (a, b) if a < b else (b, a)
                self._strengthen(*key_pair)

    def _strengthen(self, a, b):
        row = self.conn.execute(
            "SELECT w FROM weights WHERE a=? AND b=?", (a, b)
        ).fetchone()
        w = row[0] if row else 0.0
        w = w + self.eta * (1 - w)  # Hebbian
        self.conn.execute(
            "INSERT OR REPLACE INTO weights (a, b, w) VALUES (?, ?, ?)", (a, b, w)
        )
        self.conn.commit()

    def related(self, entity, top=5):
        """Сущности, ассоциированные с данной, по силе связи."""
        e = entity.lower().strip()
        rows = self.conn.execute(
            "SELECT a, b, w FROM weights WHERE a=? OR b=? ORDER BY w DESC LIMIT ?",
            (e, e, top)
        ).fetchall()
        out = []
        for a, b, w in rows:
            other = b if a == e else a
            out.append({"entity": other, "weight": round(w, 3)})
        return out

    def close(self):
        self.conn.close()
