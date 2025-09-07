from typing import Iterable, List


def split_text_by_chars(text: str, max_chars: int = 12000, overlap: int = 200) -> List[str]:
    if max_chars <= 0:
        return [text]
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    start = 0
    end = len(text)
    while start < end:
        stop = min(start + max_chars, end)
        chunk = text[start:stop]
        chunks.append(chunk)
        if stop >= end:
            break
        start = stop - overlap if overlap > 0 else stop
    return chunks


def iter_nonempty(parts: Iterable[str]) -> Iterable[str]:
    for p in parts:
        if p and p.strip():
            yield p

