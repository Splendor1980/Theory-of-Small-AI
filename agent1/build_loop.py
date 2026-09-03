"""Замкнутая петля «генерация -> проверка -> ошибка -> память -> починка».

Философия (по тезисам ПЛАНОВЫЕ-ИДЕИ.md):
  - скелет-«рельсы» (templates) + микро-правки внутри функций
  - Error Explainer переводит лог в человеческую инструкцию
  - лоботомия контекста: каждая итерация - чистый запрос (не тянем старый код)
  - каждая пойманная ошибка оседает в граф как трипл  (<фича> fails_with <суть>)
  - детектор зацикливания прекращает петлю (микро-модель может циклИться)

Под Godot (опция): godot --headless --check-only. Без Godot: мини-валидатор.
"""
import argparse
import os
import re
import sys

from .gd_validator import validate_script, _strip_comment, DECLARATION
from .tools.error_explainer import ErrorExplainer
from .core import template_library, theme_library

MAX_ITER = 6


def generate_initial(idea, agent):
    """Первый прогон через память-управляемую генерацию."""
    return agent.answer(idea)


def auto_fix(code, errors, explainer, agent, idea):
    """Авто-починка по категориям ошибок (без LLM, «код в рельсы шаблона»).

    Возвращает (новый_код, список_применённых_фиксов).
    """
    lines = code.splitlines()
    fixes = []
    lines_changed = True
    guard = 0

    while lines_changed and guard < 12:
        lines_changed = False
        guard += 1
        try:
            errs = validate_script("\n".join(lines))
        except Exception:
            break
        if not errs:
            break
        err = errs[0]
        cat = err["category"]
        ln = err["line"]
        msg = err["message"]

        if cat == "undeclared" and ln >= 0:
            m = re.search(r'Переменная "(\w+)" не объявлена', msg)
            if m:
                name = m.group(1)
                ind = _indent(lines[ln - 1]) if ln - 1 < len(lines) else ""
                decl = f"{ind}var {name} = 0  # auto-fix: declared"
                insert_at = ln - 1
                if DECLARATION.search(lines[insert_at]):
                    decl = f"{ind}# auto-fix noted: {name}"
                lines.insert(insert_at, decl)
                fixes.append(f"объявил переменную '{name}' перед строкой {ln}")
                lines_changed = True
                continue

        elif cat in ("bracket", "string"):
            if ln >= 0:
                fixes.append(f"строка {ln}: {msg} (требуется ручная правка)")
                lines_changed = False
                break

        else:
            fixes.append(f"{msg}")
            break

    # записать ошибки в память после попытки
    return "\n".join(lines), fixes, err_detail(errs) if errs else None


def err_detail(errs):
    if not errs:
        return None
    e = errs[0]
    return f'{e["category"]}: {e["message"]}'


def _indent(line):
    m = re.match(r"^\s*", line)
    return m.group(0) if m else ""


def _extract_problem_from_fix(idea, fix_list):
    """Собрать суть ошибки для сохранения в граф."""
    return "; ".join(fix_list) if fix_list else "unknown"


def _ensure_memory_triples(agent, idea, fix_list, detail):
    """Осесть в граф:  (<фича> fails_with <суть>)."""
    feature = idea.strip().lower().replace(" ", "_")[:40] or "task"
    summary = (detail or _extract_problem_from_fix(idea, fix_list))[:200]
    agent.memory.kg.add(feature, "fails_with", summary, source="build_loop")


def build(idea, agent, data_dir="_data", with_godot=False):
    explainer = ErrorExplainer()
    history = []

    # Быстрый путь: если идея совпала с играбельным шаблоном из библиотеки,
    # выдаём полноценную игру сразу (без скелета и авто-починки).
    tpl_name, tpl_code = template_library.resolve_template(idea)
    if tpl_code is not None:
        theme_name, _theme = theme_library.pick_theme(idea)
        tpl_code = theme_library.apply_theme(tpl_code, idea=idea)
        errors = validate_script(tpl_code)
        agent.memory.remember_turn(idea, [tpl_name, theme_name, "template"])
        return {
            "ok": not errors, "code": tpl_code, "iterations": 0,
            "idea": idea, "template": tpl_name,
            "template_label": template_library.template_label(idea),
            "theme": theme_name,
            "history": history, "errors": errors,
            "memory_size": agent.memory.kg.count(),
        }

    # Итерация 0: чистая генерация (лоботомия: никакого старого кода в запросе)
    res = generate_initial(idea, agent)
    code = res["skeleton"]
    history.append({"iter": 0, "code": code, "errors": [], "fixes": []})

    for it in range(1, MAX_ITER + 1):
        errors = validate_script(code)
        if not errors:
            return {
                "ok": True, "code": code, "iterations": it,
                "idea": idea, "history": history,
                "memory_size": agent.memory.kg.count(),
            }

        # Поймали ошибку -> стенограмма для модели/правил (чистый запрос)
        raw = errors[0]["message"]
        instruction, cat = explainer.explain(raw)
        agent.memory.remember_turn(idea, [raw, instruction or raw, cat or "err"])

        if explainer.is_looping(raw):
            # зацикливание: не мучаем, записываем и выходим
            _ensure_memory_triples(agent, idea, [f"loop on: {instruction}"], raw[:120])
            return {
                "ok": False, "code": code, "iterations": it,
                "idea": idea, "error": f"зацикливание на: {instruction or raw}",
                "history": history, "memory_size": agent.memory.kg.count(),
            }

        # авто-починка (внутри рельс скелета)
        new_code, fixes, detail = auto_fix(code, errors, explainer, agent, idea)
        history.append({"iter": it, "code": new_code, "errors": errors, "fixes": fixes})

        if not fixes:
            # не смогли авто-починить -> сохраняем в память и выходим
            _ensure_memory_triples(agent, idea, [instruction or raw], raw[:120])
            return {
                "ok": False, "code": new_code, "iterations": it,
                "idea": idea, "error": instruction or raw,
                "history": history, "memory_size": agent.memory.kg.count(),
            }

        code = new_code

    return {
        "ok": False, "code": code, "iterations": MAX_ITER,
        "idea": idea, "error": "исчерпан лимит итераций",
        "history": history, "memory_size": agent.memory.kg.count(),
    }


def main():
    ap = argparse.ArgumentParser(description="Agent 1 - feedback loop generator")
    ap.add_argument("idea", nargs="+", help="game idea")
    ap.add_argument("--out", default=None)
    ap.add_argument("--iter", type=int, default=MAX_ITER)
    ap.add_argument("--seed", default=None)
    args = ap.parse_args()
    from .agent_loop import MemoryAwareAgent
    agent = MemoryAwareAgent()
    if args.seed:
        import json
        with open(args.seed, encoding="utf-8") as fh:
            agent.seed_from_triples(json.load(fh), source="seed")
    res = build(" ".join(args.idea), agent)
    print("== build result ==")
    print("ok:", res["ok"])
    print("iterations:", res["iterations"])
    if "error" in res:
        print("error:", res["error"])
    print("memory_size:", res["memory_size"])
    print("--- fixes по итерациям ---")
    for h in res["history"]:
        if h["fixes"]:
            print(f'  iter {h["iter"]}: {h["fixes"]}')
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "game.gd"), "w", encoding="utf-8") as fh:
            fh.write(res["code"])
        print("wrote", os.path.join(args.out, "game.gd"))
    else:
        print(res["code"])
    agent.close()
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())