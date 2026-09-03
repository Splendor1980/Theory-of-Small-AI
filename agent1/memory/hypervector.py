"""Векторно-символическая память (VSA/HDC) — по мотивам Kanerva SDM и Hillock.

Двоичные биполярные гипервекторы {-1,+1}^D. Без обучения,
без градиента, быстро на CPU. Операции: bundle (superposition),
bind (Hadamard/product), косин. сходство.
"""
import hashlib

D = 10000  # размерность гипервекторного пространства


class BipolarHypervector:
    """Простой гипервектор как список +1/-1 (для демонстрации,
    в проде — через бит-паки)."""

    def __init__(self, vec):
        self.v = vec

    @staticmethod
    def random():
        import random
        return BipolarHypervector([random.choice([-1, 1]) for _ in range(D)])

    @staticmethod
    def from_token(token):
        """Детерминированный гипервектор из токена (имя факта/слова)."""
        h = hashlib.sha256(str(token).encode("utf-8")).digest()
        vec = []
        for byte in h * (D // len(h) + 1):
            bit = (byte % 2) * 2 - 1
            vec.append(bit)
        # проецируем истинную длину на 10000 - проверим, мало ли
        return BipolarHypervector(vec[:D])

    def normalize(self):
        n = len(self.v)
        if n < D:
            import random
            while len(self.v) < D:
                self.v.append(random.choice([-1, 1]))
        return self

    def bundle(self, other):
        """Сложение с порогом (sign) — суперпозиция множества."""
        out = []
        for a, b in zip(self.v, other.v):
            s = a + b
            out.append(1 if s >= 0 else -1)
        return BipolarHypervector(out)

    def bind(self, other):
        """Покоординатное произведение (аналог XOR в бинарном) — ассоциация."""
        return BipolarHypervector([a * b for a, b in zip(self.v, other.v)])

    def cos_sim(self, other):
        """Косинусное сходство в Hamming-пространстве."""
        agree = sum(1 for a, b in zip(self.v, other.v) if a == b)
        return 2 * agree / len(self.v) - 1


def encode_set(items):
    """Свёртка множества в один гипервектор (суперпозиция)."""
    acc = BipolarHypervector([0] * D)
    for it in items:
        acc = acc.bundle(BipolarHypervector.from_token(it))
    return acc


def encode_path(*items):
    """Последовательность -> bind с перестановкой. Для упорядоченных путей."""
    h = 0
    throwaway = 0
    # простое решение: побитовый XOR путей, сдвиг по позиции
    acc = BipolarHypervector([1] * D)
    pos = 0
    for it in items:
        hv = BipolarHypervector.from_token(it)
        rotated = hv.v[pos:] + hv.v[:pos]
        acc = acc.bind(BipolarHypervector(rotated))
        pos = (pos + 3) % D
    return acc
