"""Готовит Godot-проект под конкретную игру для облачной APK-сборки (stdlib-only).

Мост между Agent 1 и CI: берёт идею, находит шаблон через template_library,
применяет тему через theme_library, кладёт игру в project/games/, выставляет
GAME_NAME в main.gd. Затем CI (ci/build-apk.yml) экспортит APK в облаке.

Использование:
    python -m agent1.tools.make_project "змейка на конфетах" [--out DIR]
"""
import argparse
import os
import re
import shutil
import sys

# корень agent1
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agent1.core import template_library, theme_library


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def build_project(idea, out_dir=None):
    """Собрать папку Godot-проекта под идею. Вернуть dict-итог."""
    tpl_name, tpl_code = template_library.resolve_template(idea)
    if tpl_code is None:
        return {
            "ok": False,
            "reason": f"нет шаблона под идею: {idea!r}",
            "template": None, "theme": None, "out": None,
        }

    theme_name, _theme = theme_library.pick_theme(idea)
    game_code = theme_library.apply_theme(tpl_code, idea=idea)

    project_src = os.path.join(ROOT, "project")
    if out_dir is None:
        out_dir = os.path.join(ROOT, "build", "project")
    games_dir = os.path.join(out_dir, "games")

    # копируем каркас проекта (кроме старых игр), затем кладём выбранную игру
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(games_dir, exist_ok=True)
    for f in os.listdir(project_src):
        src = os.path.join(project_src, f)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(out_dir, f))

    game_dst = os.path.join(games_dir, f"{tpl_name}.gd")
    _write(game_dst, game_code)

    # выставляем GAME_NAME в main.gd
    main_path = os.path.join(out_dir, "main.gd")
    main_src = _read(main_path)
    main_src = main_src.replace('GAME_NAME_PLACEHOLDER', tpl_name)
    _write(main_path, main_src)

    return {
        "ok": True,
        "reason": "ok",
        "template": tpl_name,
        "theme": theme_name,
        "out": out_dir,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("idea", help="идея игры, напр. «змейка на конфетах»")
    ap.add_argument("--out", default=None, help="куда собрать проект (по умолчанию build/project)")
    args = ap.parse_args(argv)

    r = build_project(args.idea, args.out)
    print("template:", r.get("template"))
    print("theme   :", r.get("theme"))
    print("out     :", r.get("out"))
    print("ok      :", r.get("ok"))
    if not r.get("ok"):
        print("reason  :", r.get("reason"))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
