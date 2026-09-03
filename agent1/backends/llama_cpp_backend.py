"""Бэкенд на llama.cpp (GGUF-модели, включая Mamba2-Code).

Подключается лениво: если пакет llama_cpp не установлен или веса не найдены,
бэкенд недоступен с понятной ошибкой.

Mamba2-Code (527k) — тестовая модель. Её практический смысл в проверке
конвейера «промпт -> GGUF -> JSON -> GDScript». Идеальная цель для этой
архитектуры — компактный код-инструкт GGUF (например Qwen2.5-Coder-0.5B-Instruct).
"""

import os


class LlamaCppBackend:
    name = "llama_cpp"

    def __init__(self, model_path: str, n_ctx: int = 1024, n_threads: int = 4):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self._llm = None
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                "GGUF model not found: %s" % model_path
            )
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "llama-cpp-python not installed. Run: "
                "pip install llama-cpp-python"
            ) from exc
        self._llm = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads,
                          verbose=False)

    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        if self._llm is None:
            raise RuntimeError("Backend not initialized")
        out = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.1,
            top_p=0.9,
            stop=["\n\nHuman", "</s>"],
        )
        return out["choices"][0]["text"].strip()

    def __repr__(self) -> str:
        return "<llama_cpp backend: %s>" % os.path.basename(self.model_path)
