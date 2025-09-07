import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from dotenv import load_dotenv

from translator.utils import translate_documents, detect_direction


load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "translated"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

for d in (UPLOAD_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=str(STATIC_DIR),
    )

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/upload")
    def upload():
        files = request.files.getlist("files")
        mode = request.form.get("mode", "auto")  # 'en-fr', 'fr-en', or 'auto'

        if not files:
            return redirect(url_for("index"))

        saved_paths = []
        for f in files:
            if not f or not f.filename:
                continue
            filename = f.filename
            # Ensure unique name to avoid collisions
            unique = f"{uuid.uuid4().hex[:8]}__{filename}"
            dest = UPLOAD_DIR / unique
            f.save(dest)
            saved_paths.append(dest)

        # Translate synchronously for simplicity
        outputs = translate_documents(
            inputs=saved_paths,
            mode=mode,
            output_dir=OUTPUT_DIR,
        )

        # Prepare display info
        result_items = []
        for item in outputs:
            result_items.append({
                "source_name": Path(item["source"]).name,
                "output_name": Path(item["output"]).name,
                "output_url": url_for("download_translated", filename=Path(item["output"]).name),
                "direction": item["direction"],
            })

        return render_template("result.html", results=result_items)

    @app.get("/translated/<path:filename>")
    def download_translated(filename: str):
        return send_from_directory(OUTPUT_DIR, filename, as_attachment=False)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)

