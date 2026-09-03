"""Оркестратор: граф знаний + HDC-ворота + Hebbian-ассоциация.

Трёхслойная память:
  1. KnowledgeGraph — факты (SPO)
  2. Hypervector (VSA/HDC) — быстрый семантический барьер
  3. Hebbian — ассоциативная близость сущностей
"""
import os
from .knowledge_graph import KnowledgeGraph
from .hebbian import HebbianMemory
from .hypervector import BipolarHypervector, encode_set

GATE_THRESHOLD = 0.4


class Memory:
    def __init__(self, data_dir="_data"):
        os.makedirs(data_dir, exist_ok=True)
        self.kg = KnowledgeGraph(os.path.join(data_dir, "knowledge.db"))
        self.hebb = HebbianMemory(os.path.join(data_dir, "hebbian.db"))
        self.gate = {}  # token -> BipolarHypervector (кеш)

    def ingest_triples(self, triples, source=None):
        return self.kg.add_batch(triples, source)

    def _hv(self, token):
        if token not in self.gate:
            self.gate[token] = BipolarHypervector.from_token(token)
        return self.gate[token]

    def query(self, question, top=5):
        """Приоритет: точный факт -> Hebbian-ассоциация -> LIKE."""
        # 1) точный субъект
        q = question.lower().strip()
        facts = self.kg.query_subject(q)
        if facts:
            return {"mode": "exact", "facts": facts}

        # 2) LIKE по словам
        fuzzy = self.kg.query_text(question)
        if fuzzy:
            return {"mode": "fuzzy", "facts": fuzzy[:top]}

        # 3) Hebbian-ассоциации
        rel = self.hebb.related(q, top)
        if rel:
            gathered = []
            for r in rel:
                gathered.extend(self.kg.query_subject(r["entity"]))
            return {"mode": "hebbian", "facts": gathered[:top]}

        return {"mode": "none", "facts": []}

    def gate_score(self, question, facts):
        """HDC-ворота: насколько вопрос похож на доступные факты.
        Возвращает от 0..1. Ниже порога => отказ."""
        if not facts:
            return 0.0
        qhv = encode_set(question.lower().split())
        scores = []
        for f in facts:
            fhv = encode_set([f["subject"], f["predicate"], f["object"]])
            scores.append(qhv.cos_sim(fhv))
        return max(scores) if scores else 0.0

    def remember_turn(self, question, entities):
        """Hebbian-фиксация связей после диалогового хода."""
        self.hebb.coactivate([question] + entities)

    def close(self):
        self.kg.close()
        self.hebb.close()
