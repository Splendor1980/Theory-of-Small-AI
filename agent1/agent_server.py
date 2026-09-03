"""OpenAI-совместимый HTTP-сервер для Agent 1 (stdlib-only).

Поднимает локальный endpoint, чтобы opencode мог подключить Agent 1
как «модель» в выборе. Реализует:
  GET  /v1/models           -> список моделей ({id: 'agent1'})
  POST /v1/chat/completions -> ответ в OpenAI-формате (stream/non-stream)

Без зависимостей: только http.server + json. Запуск:
    python agent_server.py --port 8971 --data _data --seed seed_gdd.json

После старта opencode подключается через:
    provider.agent1.baseURL = http://127.0.0.1:8971/v1
"""
import argparse
import json
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent1.memory.orchestrator import Memory  # noqa: E402
from agent1.backends.rule_backend import RuleBackend, KEYWORDS  # noqa: E402
from agent1.core.schema import GameIntent  # noqa: E402
from agent1.core.generator import render_skeleton  # noqa: E402

MODEL_ID = "agent1"
MODEL_NAME = "Agent 1 (offline symbolic)"
AGENT_READY = {"ready": False, "memory": None}


def _load_seed(memory, path):
    if not path or not Path(path).exists():
        return
    try:
        with open(path, encoding="utf-8") as fh:
            triples = json.load(fh)
        memory.kg.add_batch(triples, source="seed")
        print(f"[agent1-server] seeded {len(triples)} triples from {path}")
    except Exception as exc:  # noqa: BLE001
        print(f"[agent1-server] seed failed: {exc}")


def chat_reply(question):
    """Отвечать в чате: память-управляемая генерация + пояснение."""
    mem = AGENT_READY["memory"]
    rule = RuleBackend()
    try:
        raw = rule.complete("SYSTEM\nPlayer idea: {q}\nJSON:".format(q=question))
        data = json.loads(raw)
    except (TypeError, ValueError):
        data = {}
    intent_dict = dict(data)
    res = mem.query(question)
    facts = res.get("facts", [])
    for f in facts:
        s, p, o = f["subject"], f["predicate"], f["object"]
        if p == "is" and s in {"genre", "genres"} and o in KEYWORDS["genre"]:
            intent_dict["genre"] = o
        elif p == "is" and s in {"scheme", "color", "color_scheme"} and o in KEYWORDS["color_scheme"]:
            intent_dict["color_scheme"] = o
        elif p == "is" and s in {"level", "level_type"} and o in KEYWORDS["level_type"]:
            intent_dict["level_type"] = o

    tokens = [f["subject"] for f in facts] + [
        w for w in question.split() if len(w) > 2
    ]
    mem.remember_turn(question, tokens)

    intent = GameIntent.from_dict(intent_dict)
    if not intent.is_valid:
        intent = GameIntent.from_dict({
            "genre": "platformer", "level_type": "side_scroll",
            "player_movement": "left_right", "color_scheme": "retro",
        })
    skeleton = render_skeleton(intent)

    def _serial(d):
        out = {}
        for k, v in d.items():
            out[k] = sorted(v) if isinstance(v, set) else v
        return out

    lines = ["*Agent 1 (offline symbolic)*", ""]
    lines.append(f"Запрос: `{question}`")
    lines.append(f"Память: режим `{res['mode']}`, фактов в графе: {mem.kg.count()}")
    if facts:
        lines.append("Использованные факты из памяти:")
        for f in facts[:5]:
            lines.append(f"- {f['subject']} {f['predicate']} {f['object']}")
    lines.append("")
    lines.append("Интент (валидированный):")
    lines.append(f"```json\n{json.dumps(_serial(dict(intent)), ensure_ascii=False, indent=2)}\n```")
    lines.append("Сгенерированный скелет `game.gd` (места `<HAND>` — для ручной доводки):")
    lines.append(f"```gdscript\n{skeleton}\n```")
    return "\n".join(lines)


def _model_list():
    return {
        "object": "list",
        "data": [{
            "id": MODEL_ID,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "local",
        }],
    }


def _completion(payload):
    """Синхронный ответ или генератор SSE-чанков."""
    stream = bool(payload.get("stream", False))
    messages = payload.get("messages", [])
    user_text = ""
    for m in messages:
        if m.get("role") == "user":
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                )
            user_text = content.strip() or user_text
    if not user_text:
        user_text = "Hello"
    reply = chat_reply(user_text)
    cid = "chatcmpl-" + uuid.uuid4().hex[:12]
    base = {
        "id": cid,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": MODEL_ID,
    }
    if not stream:
        base["choices"] = [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop",
        }]
        base["usage"] = {
            "prompt_tokens": len(user_text),
            "completion_tokens": len(reply),
            "total_tokens": len(user_text) + len(reply),
        }
        return base

    def sse():
        yield _first_chunk(base)
        for i in range(0, len(reply), 60):
            piece = reply[i:i + 60]
            yield {
                "id": cid, "object": "chat.completion.chunk",
                "created": int(time.time()), "model": MODEL_ID,
                "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}],
            }
        yield {
            "id": cid, "object": "chat.completion.chunk",
            "created": int(time.time()), "model": MODEL_ID,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
    return sse


def _first_chunk(base):
    import copy
    b = copy.deepcopy(base)
    b["object"] = "chat.completion.chunk"
    b["choices"] = [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]
    return b


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError:
            return {}

    def do_GET(self):
        if not AGENT_READY["ready"]:
            # быстрый GET до готовности: отдаём список моделей как есть
            pass
        if self.path.split("?")[0] in ("/v1/models", "/models"):
            self._send_json(_model_list())
        else:
            self._send_json({"error": {"message": "not found", "type": "invalid_request_error"}}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in ("/v1/chat/completions", "/chat/completions"):
            self._send_json({"error": {"message": "not found"}, "type": "invalid_request_error"}, 404)
            return
        payload = self._read_body()
        try:
            result = _completion(payload)
        except Exception as exc:  # noqa: BLE001
            self._send_json({
                "error": {"message": str(exc), "type": "server_error"}
            }, 500)
            return
        if callable(result):  # SSE generator
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            for chunk in result():
                self.wfile.write(("data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n").encode("utf-8"))
                self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        else:
            self._send_json(result)


def main():
    ap = argparse.ArgumentParser(description="Agent 1 OpenAI-compatible server")
    ap.add_argument("--port", type=int, default=8971)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--data", default="_data")
    ap.add_argument("--seed", default=None)
    args = ap.parse_args()

    mem = Memory(args.data)
    if args.seed:
        _load_seed(mem, args.seed)
    AGENT_READY["memory"] = mem
    AGENT_READY["ready"] = True

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[agent1-server] listening on http://{args.host}:{args.port}/v1")
    print(f"[agent1-server] model id: '{MODEL_ID}'")
    print("[agent1-server] press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        mem.close()


if __name__ == "__main__":
    main()