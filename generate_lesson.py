"""
Picks today's lesson from texts.json (rotating by date, so the whole
list cycles before repeating) and writes it out as a dated, standalone
HTML page under docs/lessons/YYYY-MM-DD.html for GitHub Pages to serve.

Also maintains:
  - docs/lessons.json  - a manifest of every lesson generated so far
  - docs/index.html    - a home page listing all of them, newest first
  - docs/meta.json      - today's date/topic/path, used by send_telegram.py

Each lesson page shows the English text plus a "He terminado de
traducir" button. Clicking it reveals the Spanish translation, grammar
notes, and vocabulary notes - all hidden until then.

No external dependencies - standard library only.
"""

import datetime
import html
import json
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
TEXTS_PATH = BASE_DIR / "texts.json"
DOCS_DIR = BASE_DIR / "docs"
LESSONS_DIR = DOCS_DIR / "lessons"
MANIFEST_PATH = DOCS_DIR / "lessons.json"
INDEX_PATH = DOCS_DIR / "index.html"
META_PATH = DOCS_DIR / "meta.json"


def load_texts():
    with open(TEXTS_PATH, "r", encoding="utf-8") as f:
        texts = json.load(f)
    if not texts:
        raise RuntimeError(f"{TEXTS_PATH} is empty - add some texts first.")
    return texts


def pick_todays_entry(texts):
    """
    Deterministic pick based on the date: every day gets a different
    entry, and the full list cycles through before anything repeats.
    Re-running the workflow later the same day gives the same entry.
    """
    day_index = datetime.date.today().toordinal()
    return texts[day_index % len(texts)]


def esc(text: str) -> str:
    """HTML-escape and turn newlines into <br> for display."""
    return html.escape(text or "").replace("\n", "<br>")


LESSON_STYLE = """
  :root { color-scheme: light dark; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 700px;
    margin: 40px auto;
    padding: 0 20px 60px;
    line-height: 1.6;
  }
  .tag {
    display: inline-block;
    background: #e8edff;
    color: #2a3a7a;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.8em;
    margin-bottom: 14px;
  }
  h1 { font-size: 1.35em; margin-top: 0; }
  .card {
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 20px;
    margin: 16px 0;
  }
  .section-title {
    font-weight: 600;
    margin-top: 0;
    margin-bottom: 8px;
    color: #555;
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  button {
    background: #2a6df5;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 10px;
    font-size: 1em;
    cursor: pointer;
    width: 100%;
  }
  button:hover { background: #1c54c9; }
  .hidden { display: none; }
  a { color: #2a6df5; }
  @media (prefers-color-scheme: dark) {
    .card { border-color: #333; }
    .tag { background: #26305c; color: #cfd8ff; }
  }
"""


def render_lesson_html(entry: dict, date_str: str) -> str:
    topic = esc(entry.get("topic", ""))
    english = esc(entry.get("english_text", ""))
    spanish = esc(entry.get("spanish_translation", ""))
    grammar = esc(entry.get("grammar_notes", ""))
    vocab = esc(entry.get("vocabulary_notes", ""))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lección - {date_str}</title>
<style>{LESSON_STYLE}</style>
</head>
<body>
  <p><a href="../index.html">&larr; Todas las lecciones</a></p>
  <div class="tag">{date_str}</div>
  <h1>{topic}</h1>

  <div class="card">
    <p>{english}</p>
  </div>

  <button id="reveal-btn" onclick="
    document.getElementById('answer').classList.remove('hidden');
    document.getElementById('reveal-btn').style.display = 'none';
  ">
    He terminado de traducir
  </button>

  <div id="answer" class="hidden">
    <div class="card">
      <div class="section-title">Traducción</div>
      <p>{spanish}</p>
    </div>
    <div class="card">
      <div class="section-title">Notas de gramática</div>
      <p>{grammar}</p>
    </div>
    <div class="card">
      <div class="section-title">Notas de vocabulario</div>
      <p>{vocab}</p>
    </div>
  </div>
</body>
</html>
"""


def render_index_html(manifest: list) -> str:
    rows = "\n".join(
        f'    <li><span class="tag">{item["date"]}</span> '
        f'<a href="lessons/{item["date"]}.html">{esc(item["topic"])}</a></li>'
        for item in manifest
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lecciones de español</title>
<style>
{LESSON_STYLE}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
  .tag {{ margin-right: 10px; }}
</style>
</head>
<body>
  <h1>Lecciones de español</h1>
  <ul>
{rows}
  </ul>
</body>
</html>
"""


def load_manifest() -> list:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def update_manifest(manifest: list, date_str: str, topic: str) -> list:
    # Remove any existing entry for today (handles same-day reruns), then add it back
    manifest = [item for item in manifest if item["date"] != date_str]
    manifest.append({"date": date_str, "topic": topic})
    manifest.sort(key=lambda item: item["date"], reverse=True)
    return manifest


def main():
    texts = load_texts()
    entry = pick_todays_entry(texts)
    date_str = datetime.date.today().isoformat()
    topic = entry.get("topic", "")

    LESSONS_DIR.mkdir(parents=True, exist_ok=True)

    lesson_path = LESSONS_DIR / f"{date_str}.html"
    lesson_path.write_text(render_lesson_html(entry, date_str), encoding="utf-8")

    manifest = update_manifest(load_manifest(), date_str, topic)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    INDEX_PATH.write_text(render_index_html(manifest), encoding="utf-8")

    META_PATH.write_text(
        json.dumps(
            {"date": date_str, "topic": topic, "path": f"lessons/{date_str}.html"},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Generated lesson for {date_str}: {topic}")


if __name__ == "__main__":
    main()
