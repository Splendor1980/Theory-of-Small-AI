"""Подтягивание знаний из интернета в граф (stdlib-only).

«Ум из интернета, а не из весов»: скачиваем страницу документации/туториала,
вытаскиваем из неё осмысленные триплы (Subject is Object), складываем в
KnowledgeGraph. Работает без requests/bs4 — только urllib + html.parser,
чтобы не тянуть зависимости на слабых машинах.
"""
import re
import urllib.request
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (X11; Linux x86_64; rv:109.0) "
      "Gecko/20100101 Firefox/119.0")

# Курируемые страницы Godot-документации (надёжнее, чем поиск).
CURATED = {
    "2d movement": [
        "https://docs.godotengine.org/en/stable/tutorials/physics/using_character_body_2d.html",
        "https://docs.godotengine.org/en/stable/tutorials/2d/2d_movement.html",
    ],
    "physics": [
        "https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html",
    ],
}


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


class _TextExtract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)


def html_to_text(html):
    p = _TextExtract()
    p.feed(html)
    return " ".join(" ".join(p.text).split())


def _split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _subj_is_obj(sent):
    """Одна фраза -> пары (субъект, объект) для 'X is/...) Y'."""
    pats = [
        r"([A-Z][A-Za-z0-9_ .\)]{1,40}?)\s+is\s+(?:an? |the )?([a-z][A-Za-z0-9_ .'-]{1,60})",
    ]
    for pat in pats:
        for m in re.finditer(pat, sent):
            s = m.group(1).strip().rstrip(".")
            o = m.group(2).strip().rstrip(".")
            if s and o:
                yield s, o


def page_to_triples(url, max_triples=30):
    html = fetch(url)
    text = html_to_text(html)
    triples = []
    for sent in _split_sentences(text):
        for s, o in _subj_is_obj(sent):
            triples.append((s, "is", o))
            if len(triples) >= max_triples:
                return triples
    return triples


def ingest_curated(memory, topic, max_per_page=25):
    """Загрузить курируемую страницу по теме в граф. Вернуть кол-во добавленных."""
    urls = CURATED.get(topic.lower(), [])
    total = 0
    for url in urls:
        try:
            for s, p, o in page_to_triples(url, max_triples=max_per_page):
                memory.kg.add(s, p, o, source=url)
                total += 1
        except Exception:
            continue
    return total
