"""Поиск по интернету без API-ключей (stdlib-only).

DuckDuckGo HTML-эндпоинт -> список ссылок. Затем web_knowledge.fetch
скачивает страницы и извлекает триплы в граф.
"""
import re
import urllib.parse
import urllib.request
from .web_knowledge import fetch, html_to_text, _split_sentences

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

_UDDG = re.compile(r"uddg=([^&]+)")


def search_links(query, count=5):
    """Вернуть список URL по запросу через DuckDuckGo HTML."""
    q = urllib.parse.quote(query)
    url = "https://html.duckduckgo.com/html/?q=" + q
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return []
    out, seen = [], set()
    for m in _UDDG.finditer(html):
        target = urllib.parse.unquote(m.group(1))
        if not target.startswith("http"):
            continue
        if any(b in target for b in ("duckduckgo", "bing.com", "yandex", "google")):
            continue
        if target in seen:
            continue
        seen.add(target)
        out.append(target)
        if len(out) >= count:
            break
    return out


def ingest_search(memory, query, pages=2, max_triples=40):
    """Найти страницы по запросу, вытащить триплы, загрузить в граф."""
    links = search_links(query, count=pages)
    total = 0
    for link in links:
        try:
            html = fetch(link, timeout=15)
            text = html_to_text(html)
            sents = _split_sentences(text)
            for sent in sents[:60]:
                for s, o in _subj_is_obj(sent):
                    n = memory.kg.add(s, "is", o, source=link)
                    total += n
                    if total >= max_triples:
                        return total
        except Exception:
            continue
    return total


def _subj_is_obj(sent):
    """Одна фраза -> пары (субъект, объект) для 'X is Y'."""
    for m in re.finditer(
        r"([A-Z][\w][\w /-]{1,45})\s+is\s+(?:an? |the )?([a-z][\w][\w /-]{1,70})",
        sent,
    ):
        s, o = m.group(1).strip(), m.group(2).strip().rstrip(".")
        if s and o:
            yield s.lower(), o
