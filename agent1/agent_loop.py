"""Память-управляемый агент: связывает символьную память с генерацией.

Цепочка:
  question -> Memory.query() -> [mode, facts]
            -> rule backend + факты из памяти (уточняют дефолты)
            -> Hebbian-фиксация хода
            -> GameIntent -> render_skeleton -> .gd
"""
import os
import json

from .memory.orchestrator import Memory
from .backends.rule_backend import RuleBackend, KEYWORDS
from .core.schema import GameIntent
from .core.generator import render_skeleton


class MemoryAwareAgent:
    def __init__(self, data_dir="_data"):
        self.memory = Memory(data_dir)
        self.rule = RuleBackend()

    def seed_from_triples(self, triples, source=None):
        return self.memory.ingest_triples(triples, source)

    def _facts_override(self, text, intent_dict):
        """Факты из памяти меняют значения intent, если совпал контекст."""
        res = self.memory.query(text)
        facts = res.get("facts", [])
        for f in facts:
            s, p, o = f["subject"], f["predicate"], f["object"]
            # правило: "genre is platformer" -> genre=platformer
            if p == "is" and s in {"genre", "genres"} and o in KEYWORDS["genre"]:
                intent_dict["genre"] = o
            elif p == "is" and s in {"scheme", "color", "color_scheme"} and o in KEYWORDS["color_scheme"]:
                intent_dict["color_scheme"] = o
            elif p == "is" and s in {"level", "level_type"} and o in KEYWORDS["level_type"]:
                intent_dict["level_type"] = o
            elif p == "is" and s in {"enemy", "enemy_behavior"} and o in KEYWORDS["enemy_behavior"]:
                intent_dict["enemy_behavior"] = o
            elif p == "is" and s in {"kind", "enemy_kind"} and o in KEYWORDS["enemy_kind"]:
                intent_dict["enemy_kind"] = o
        return intent_dict, res["mode"], facts

    def answer(self, question, out_dir=None):
        raw = self.rule.complete(
            "SYSTEM\nPlayer idea: {q}\nJSON:".format(q=question)
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        intent_dict = data

        # память уточняет
        intent_dict, mode, facts = self._facts_override(question, intent_dict)

        fake = GameIntent.from_dict(intent_dict)
        # фиксируем ход в память
        tokens = [f["subject"] for f in facts] + [w for w in question.split() if len(w) > 2]
        self.memory.remember_turn(question, tokens)

        if not fake.is_valid:
            fake = GameIntent.from_dict({
                "genre": "platformer", "level_type": "side_scroll",
                "player_movement": "left_right", "color_scheme": "retro",
            })

        skeleton = render_skeleton(fake)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, "game.gd"), "w", encoding="utf-8") as fh:
                fh.write(skeleton)

        return {
            "mode": mode,
            "facts_used": facts,
            "intent": dict(fake),
            "skeleton": skeleton,
            "memory_size": self.memory.kg.count(),
        }

    def close(self):
        self.memory.close()


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Agent 1 - memory-driven GDScript generator")
    ap.add_argument("idea", nargs="+", help="game idea words")
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", default=None,
                    help="path to JSON file with list of [s,p,o] triples to ingest")
    args = ap.parse_args()
    question = " ".join(args.idea)
    agent = MemoryAwareAgent()
    if args.seed:
        with open(args.seed, encoding="utf-8") as fh:
            triples = json.load(fh)
        agent.seed_from_triples(triples, source="seed")
    res = agent.answer(question, out_dir=args.out)
    print("== result ==".encode("utf-8").decode("utf-8"))
    print("memory_mode:", res["mode"])
    print("facts_used:", res["facts_used"])
    print("intent:", res["intent"])
    print("memory_size:", res["memory_size"])
    print(res["skeleton"])
    agent.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
