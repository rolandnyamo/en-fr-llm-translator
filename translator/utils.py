import os
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable, List, Literal, Optional, Sequence, Tuple, Union

from .chunking import split_text_by_chars, iter_nonempty
from .extractors import extract_text_from_file


Direction = Literal["en-fr", "fr-en"]


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(name)
    return val if val is not None else default


def _openai_client():
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError(
            "The `openai` package is required. Install with `pip install openai`"
        ) from e

    api_key = _get_env("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. Set it in environment or .env file."
        )
    base_url = _get_env("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url)
    return client


def detect_direction(text_sample: str, default: Direction = "en-fr") -> Direction:
    sample = (text_sample or "").strip()
    if not sample:
        return default
    # Very simple heuristic: count ASCII letters vs accented letters / common French words
    sample_lower = sample.lower()
    french_markers = [" le ", " la ", " les ", " et ", " un ", " une ", " des ", " à ", " pour ", " avec "]
    score = sum(1 for m in french_markers if m in f" {sample_lower} ")
    # If accents present, likely French
    has_accents = any(c in sample for c in "àâçéèêëîïôùûüÿœæÀÂÇÉÈÊËÎÏÔÙÛÜŸŒÆ")
    if score > 1 or has_accents:
        return "fr-en"
    return "en-fr"


def translate_text(
    text: str,
    direction: Direction = "en-fr",
    model: Optional[str] = None,
    max_chars: Optional[int] = None,
) -> str:
    """
    Translate an arbitrary text using OpenAI Responses API, chunking as needed.
    Returns translated text concatenated in order.
    """
    if not text:
        return ""
    model = model or _get_env("OPENAI_MODEL", "gpt-4o-mini")
    max_chars = int(_get_env("TRANSLATION_MAX_CHARS", str(max_chars or 12000)))

    client = _openai_client()

    system = (
        "You are a professional translator. Translate the user text accurately "
        "and preserve line breaks. Only return the translated text without extra commentary."
    )
    if direction == "en-fr":
        task = "Translate the following English text to French."
    else:
        task = "Traduisez le texte français suivant en anglais."

    chunks = split_text_by_chars(text, max_chars=max_chars, overlap=200)
    outputs: List[str] = []
    for chunk in iter_nonempty(chunks):
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{task}\n\n{chunk}"},
            ],
        )
        # Collect text output
        out = resp.output_text or ""
        outputs.append(out.strip())

    return "\n".join(outputs)


def translate_text_stream(
    text: str,
    direction: Direction = "en-fr",
    model: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Stream translated text chunks using Responses stream. Useful for CLI or SSE.
    """
    model = model or _get_env("OPENAI_MODEL", "gpt-4o-mini")
    client = _openai_client()

    system = (
        "You are a professional translator. Translate the user text accurately "
        "and preserve line breaks. Only return the translated text without extra commentary."
    )
    if direction == "en-fr":
        task = "Translate the following English text to French."
    else:
        task = "Traduisez le texte français suivant en anglais."

    with client.responses.stream(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"{task}\n\n{text}"},
        ],
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta
        # Ensure stream completed
        _ = stream.get_final_response()


def _default_output_name(source: Path, direction: Direction) -> Path:
    # Build a new filename alongside the source, as plain text output
    return source.parent / f"{source.stem}.{direction}.translated.txt"


def translate_documents(
    inputs: Sequence[Union[str, Path]],
    mode: Literal["en-fr", "fr-en", "auto"] = "auto",
    output_dir: Optional[Union[str, Path]] = None,
    model: Optional[str] = None,
) -> List[dict]:
    """
    Translate one or more files and save results next to output_dir (or alongside each file).

    Returns: list of dicts with {source, output, direction} paths as strings.
    """
    output_dir = Path(output_dir) if output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    results: List[dict] = []
    for p in inputs:
        path = Path(p)
        text = extract_text_from_file(path)

        # Decide direction
        if mode == "auto":
            # Use a small sample to detect
            sample = text[:2000]
            direction = detect_direction(sample)
        else:
            direction = mode  # type: ignore

        translated = translate_text(text, direction=direction, model=model)

        out_path = (
            (Path(output_dir) / _default_output_name(path, direction).name)
            if output_dir
            else _default_output_name(path, direction)
        )
        out_path.write_text(translated, encoding="utf-8")

        results.append({
            "source": str(path.resolve()),
            "output": str(out_path.resolve()),
            "direction": direction,
        })

    return results
