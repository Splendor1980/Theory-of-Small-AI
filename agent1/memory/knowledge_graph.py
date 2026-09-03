"""SQLite-хранилище фактов: Subject-Predicate-Object триплы.

Hillock-style: факты в реляционной БД, не в векторах.
Точные ответы на точные вопросы без приближенного поиска.
"""
import sqlite3


class KnowledgeGraph:
    def __init__(self, db_path="knowledge.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS triples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_spo ON triples(subject, predicate)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_subj ON triples(subject)")
        self.conn.commit()

    def add(self, subject, predicate, obj, source=None):
        cur = self.conn.execute(
            "INSERT INTO triples (subject, predicate, object, source) VALUES (?, ?, ?, ?)",
            (subject.lower().strip(), predicate.lower().strip(), obj.strip(), source)
        )
        self.conn.commit()
        return cur.lastrowid

    def add_batch(self, triples, source=None):
        count = 0
        for s, p, o in triples:
            self.add(s, p, o, source)
            count += 1
        return count

    def query_subject(self, subject):
        rows = self.conn.execute(
            "SELECT predicate, object, source FROM triples WHERE subject = ?",
            (subject.lower().strip(),)
        ).fetchall()
        return [{"predicate": r[0], "object": r[1], "source": r[2]} for r in rows]

    def query_spo(self, subject=None, predicate=None, obj=None):
        conds, params = [], []
        if subject:
            conds.append("subject = ?"); params.append(subject.lower().strip())
        if predicate:
            conds.append("predicate = ?"); params.append(predicate.lower().strip())
        if obj:
            conds.append("object LIKE ?"); params.append(f"%{obj}%")
        where = " AND ".join(conds) if conds else "1=1"
        rows = self.conn.execute(
            f"SELECT subject, predicate, object, source FROM triples WHERE {where}", params
        ).fetchall()
        return [{"subject": r[0], "predicate": r[1], "object": r[2], "source": r[3]} for r in rows]

    def query_text(self, text):
        """Нефиксированный поиск по тексту (LIKE)."""
        words = text.lower().split()
        if not words:
            return []
        conds, params = [], []
        for w in words:
            conds.append("(subject LIKE ? OR predicate LIKE ? OR object LIKE ?)")
            p = f"%{w}%"
            params.extend([p, p, p])
        where = " OR ".join(conds)
        rows = self.conn.execute(
            f"SELECT subject, predicate, object, source FROM triples WHERE {where} LIMIT 20", params
        ).fetchall()
        return [{"subject": r[0], "predicate": r[1], "object": r[2], "source": r[3]} for r in rows]

    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]

    def all_subjects(self):
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT subject FROM triples ORDER BY subject"
        ).fetchall()]

    def close(self):
        self.conn.close()
