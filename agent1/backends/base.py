"""Абстракция LLM-бэкенда.

Agent 1 не должен зависеть от конкретной модели/движка. Бэкенд обязан
реализовать единственный метод `complete(prompt) -> str`.
"""

import abc


class LLMBackend(abc.ABC):
    name = "base"

    @abc.abstractmethod
    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        """Возвращает сырой текст ответа модели."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return "<%s>" % self.name
