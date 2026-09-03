"""CLI для Agent 1 (Code Generator) — generate GDScript game skeleton.

Примеры:
  python -m agent1.main "simple platformer with jumping and enemies"
  python -m agent1.main --model path/to/mamba2-code.gguf "twin stick shooter"
  python -m agent1.main --backend rule "neon puzzle with timer"

Usage:
  python -m agent1.main [-h] [--backend {rule,llama_cpp}] [--model PATH] [--out DIR] idea
"""

import argparse
import os
import sys


def _backend_by_name(name: str, model_path: str | None):
    from agent1.backends.rule_backend import RuleBackend
    if name == "rule":
        return RuleBackend()
    from agent1.backends.llama_cpp_backend import LlamaCppBackend
    if not model_path:
        raise SystemExit("--model PATH is required for backend llama_cpp")
    return LlamaCppBackend(model_path)


def run(idea: str, backend_name: str, model_path: str | None, out_dir: str | None):
    from agent1.core.prompter import build_prompt
    from agent1.core.schema import GameIntent
    from agent1.core.generator import render_skeleton, manifest_from_model_output

    backend = _backend_by_name(backend_name, model_path)

    print("[agent1] backend: %r" % backend)
    print("[agent1] idea   : %s" % idea)

    prompt = build_prompt(idea)
    raw = backend.complete(prompt)
    print("[agent1] raw model output:\n%s\n" % raw)

    default = GameIntent.from_dict({
        "genre": "platformer", "level_type": "side_scroll",
        "player_movement": "left_right", "player_shoot": "bullet",
        "enemy_behavior": "patrol", "enemy_kind": "walker",
        "color_scheme": "retro",
        "ui": ["score"], "mechanics": ["collision"],
        "players": 1, "enemies": 3, "difficulty": 2,
    })
    intent = manifest_from_model_output(raw, default_intent=default)

    if not intent.is_valid:
        print("[agent1] WARNING: intent not valid, falling back to default")
        intent = default

    skeleton = render_skeleton(intent)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "game.gd")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(skeleton)
        print("[agent1] wrote %s" % path)
    else:
        print(skeleton)

    print("[agent1] intent: %r" % dict(intent))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent 1 — Godot GDScript skeleton generator")
    ap.add_argument("idea", help="game idea in natural language (EN/RU)")
    ap.add_argument("--backend", choices=["rule", "llama_cpp"], default="rule",
                    help="LLM backend to use (default: rule fallback)")
    ap.add_argument("--model", default=None, help="path to GGUF model (llama_cpp backend)")
    ap.add_argument("--out", default=None, help="output dir for game.gd")
    args = ap.parse_args()
    try:
        return run(args.idea, args.backend, args.model, args.out)
    except Exception as exc:  # noqa: BLE001
        print("Error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
