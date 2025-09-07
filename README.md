**Translator (EN ⇄ FR)**

- Upload `.docx`, `.pdf`, or `.txt` files
- Uses OpenAI Responses API under the hood
- Saves translated files locally and provides links to open/download
- Core translation logic is a liftable utility (`translator.utils`)

Setup

- Python 3.10+
- Create and fill `.env` based on `.env.example`:
  - `cp .env.example .env` then set `OPENAI_API_KEY`
  - Optional: `OPENAI_MODEL` (default `gpt-4o-mini`), `TRANSLATION_MAX_CHARS`
- Install dependencies: `pip install -r requirements.txt`

Run

- Start server: `python app.py`
- Open: `http://localhost:5000`
- Upload files, choose direction (or Auto), and translate.
- Translated files are saved in `translated/` and linked on the results page.

Core API

- `translator.utils.translate_documents(inputs, mode="auto", output_dir="translated/", model=None)`
  - `inputs`: paths or `Path` objects
  - `mode`: `"en-fr"`, `"fr-en"`, or `"auto"` (auto-detect by heuristic)
  - Returns list of `{source, output, direction}` dicts

- `translator.utils.translate_text(text, direction="en-fr", model=None, max_chars=None) -> str`
  - Chunked translation via Responses API; preserves line breaks

- `translator.utils.translate_text_stream(text, direction="en-fr", model=None)`
  - Generator that yields streamed text deltas from Responses API

Notes

- PDF and DOCX parsing requires `pypdf` and `python-docx`.
- PDFs may lose complex formatting; output is saved as `.translated.txt`.
- For large files, text is split into chunks (configurable by `TRANSLATION_MAX_CHARS`).

