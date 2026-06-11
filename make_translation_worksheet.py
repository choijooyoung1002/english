#!/usr/bin/env python3
"""Build a printable, customizable line-by-line worksheet HTML page.

The generated page is intentionally plain HTML/CSS/JavaScript so learners can
open it in a browser, adjust spacing/font settings, and use the browser print
or PDF dialog without installing extra Python packages.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path

SOURCE = Path("content.md")
OUTPUT = Path("translation_worksheet.html")


@dataclass
class Section:
    title: str
    sentences: list[str]


def clean_inline(text: str) -> str:
    """Remove source markers and lightweight markdown while preserving Unicode."""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"【[^】]+】", "", text)
    text = text.replace("**", "")
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return " ".join(text.split())


def parse_content(markdown: str) -> tuple[str, list[Section]]:
    title = "Line-by-Line English Interpretation Worksheet"
    sections: list[Section] = []
    current: Section | None = None

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            title = clean_inline(line[2:])
        elif line.startswith("## "):
            current = Section(clean_inline(line[3:]), [])
            sections.append(current)
        elif line.startswith("- ") and current is not None:
            current.sentences.append(clean_inline(line[2:]))
    return title, sections


def build_html(title: str, sections: list[Section]) -> str:
    data = {
        "title": title,
        "sections": [section.__dict__ for section in sections],
    }
    payload = (
        json.dumps(data, ensure_ascii=False, indent=2)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return f"""<!doctype html>
<html lang=\"ko\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escape(title)} - 해석 연습지</title>
  <style>
    :root {{
      --font-size: 15px;
      --answer-lines: 4;
      --line-step: 30px;
      --item-gap: 18px;
      --page-padding: 10mm;
      --english-color: #111827;
      --muted-color: #64748b;
      --rule-color: #cbd5e1;
      --accent-color: #2563eb;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      background: #e2e8f0;
      color: #111827;
      font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
      font-size: var(--font-size);
      line-height: 1.55;
    }}

    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      align-items: end;
      padding: 14px 18px;
      border-bottom: 1px solid #cbd5e1;
      background: rgba(255, 255, 255, 0.96);
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }}

    .toolbar label {{
      display: grid;
      gap: 5px;
      color: #334155;
      font-size: 12px;
      font-weight: 700;
    }}

    .toolbar input {{
      width: 100%;
      accent-color: var(--accent-color);
    }}

    .toolbar output {{
      color: #0f172a;
      font-variant-numeric: tabular-nums;
      font-weight: 800;
    }}

    .toolbar button {{
      min-height: 38px;
      border: 0;
      border-radius: 10px;
      background: var(--accent-color);
      color: white;
      cursor: pointer;
      font-weight: 800;
    }}

    .toolbar button.secondary {{
      border: 1px solid #cbd5e1;
      background: white;
      color: #0f172a;
    }}

    .sheet {{
      width: min(100%, 210mm);
      margin: 18px auto;
      padding: var(--page-padding);
      background: white;
      box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
    }}

    header {{
      margin-bottom: 14px;
      border-bottom: 1px solid #0f172a;
      padding-bottom: 8px;
    }}

    h1 {{
      margin: 0 0 8px;
      font-size: 1.55rem;
      line-height: 1.25;
    }}

    h2 {{
      break-after: avoid;
      margin: 28px 0 12px;
      border-left: 5px solid var(--accent-color);
      padding-left: 10px;
      font-size: 1.1rem;
    }}

    .item {{
      break-inside: avoid;
      page-break-inside: avoid;
      margin-bottom: var(--item-gap);
    }}

    .sentence {{
      display: grid;
      grid-template-columns: 2em 1fr;
      gap: 6px;
      color: var(--english-color);
      font-family: Georgia, \"Times New Roman\", serif;
      font-size: 1em;
      line-height: 1.5;
    }}

    .number {{
      color: var(--accent-color);
      font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
      font-weight: 800;
      text-align: right;
    }}

    .answer-space {{
      height: calc(var(--answer-lines) * var(--line-step));
      margin-top: 5px;
      margin-left: 0;
      background-image: repeating-linear-gradient(
        to bottom,
        transparent 0,
        transparent calc(var(--line-step) - 1px),
        var(--rule-color) calc(var(--line-step) - 1px),
        var(--rule-color) var(--line-step)
      );
    }}

    @page {{
      size: A4;
      margin: 7mm;
    }}

    @media print {{
      body {{ background: white; }}
      .toolbar {{ display: none; }}
      .sheet {{
        width: auto;
        margin: 0;
        padding: 0;
        box-shadow: none;
      }}
      a {{ color: inherit; text-decoration: none; }}
    }}
  </style>
</head>
<body>
  <form class=\"toolbar\" aria-label=\"인쇄 설정\">
    <label>해석 줄 수 <output for=\"answerLines\" id=\"answerLinesValue\">4</output>
      <input id=\"answerLines\" data-var=\"--answer-lines\" data-unit=\"\" type=\"range\" min=\"2\" max=\"8\" step=\"1\" value=\"4\">
    </label>
    <label>줄 간격 <output for=\"lineStep\" id=\"lineStepValue\">30px</output>
      <input id=\"lineStep\" data-var=\"--line-step\" data-unit=\"px\" type=\"range\" min=\"22\" max=\"46\" step=\"1\" value=\"30\">
    </label>
    <label>글자 크기 <output for=\"fontSize\" id=\"fontSizeValue\">15px</output>
      <input id=\"fontSize\" data-var=\"--font-size\" data-unit=\"px\" type=\"range\" min=\"12\" max=\"20\" step=\"1\" value=\"15\">
    </label>
    <label>문항 간격 <output for=\"itemGap\" id=\"itemGapValue\">18px</output>
      <input id=\"itemGap\" data-var=\"--item-gap\" data-unit=\"px\" type=\"range\" min=\"8\" max=\"36\" step=\"1\" value=\"18\">
    </label>
    <label>페이지 여백 <output for=\"pagePadding\" id=\"pagePaddingValue\">10mm</output>
      <input id=\"pagePadding\" data-var=\"--page-padding\" data-unit=\"mm\" type=\"range\" min=\"4\" max=\"18\" step=\"1\" value=\"10\">
    </label>
    <button type=\"button\" onclick=\"window.print()\">인쇄 / PDF 저장</button>
    <button class=\"secondary\" type=\"button\" id=\"resetSettings\">기본값</button>
  </form>

  <main class=\"sheet\" id=\"worksheet\"></main>

  <script id=\"worksheet-data\" type=\"application/json\">{payload}</script>
  <script>
    const settingsKey = 'translationWorksheetSettings';
    const controls = Array.from(document.querySelectorAll('[data-var]'));
    const worksheet = document.querySelector('#worksheet');
    const data = JSON.parse(document.querySelector('#worksheet-data').textContent);

    function applyControl(control) {{
      const unit = control.dataset.unit;
      const value = `${{control.value}}${{unit}}`;
      document.documentElement.style.setProperty(control.dataset.var, value);
      document.querySelector(`#${{control.id}}Value`).textContent = value;
    }}

    function saveSettings() {{
      const values = Object.fromEntries(controls.map((control) => [control.id, control.value]));
      localStorage.setItem(settingsKey, JSON.stringify(values));
    }}

    function loadSettings() {{
      const saved = JSON.parse(localStorage.getItem(settingsKey) || '{{}}');
      controls.forEach((control) => {{
        if (saved[control.id]) control.value = saved[control.id];
        applyControl(control);
        control.addEventListener('input', () => {{
          applyControl(control);
          saveSettings();
        }});
      }});
    }}

    function renderWorksheet() {{
      let number = 1;
      worksheet.innerHTML = `
        <header>
          <h1>${{data.title}}</h1>
        </header>
      `;

      for (const section of data.sections) {{
        const sectionElement = document.createElement('section');
        sectionElement.innerHTML = `<h2>${{section.title}}</h2>`;
        for (const sentence of section.sentences) {{
          const item = document.createElement('article');
          item.className = 'item';
          item.innerHTML = `
            <div class=\"sentence\"><span class=\"number\">${{number}}.</span><span>${{sentence}}</span></div>
            <div class=\"answer-space\" aria-hidden=\"true\"></div>
          `;
          sectionElement.appendChild(item);
          number += 1;
        }}
        worksheet.appendChild(sectionElement);
      }}
    }}

    document.querySelector('#resetSettings').addEventListener('click', () => {{
      localStorage.removeItem(settingsKey);
      controls.forEach((control) => {{
        control.value = control.defaultValue;
        applyControl(control);
      }});
    }});

    loadSettings();
    renderWorksheet();
  </script>
</body>
</html>
"""


def main() -> None:
    title, sections = parse_content(SOURCE.read_text(encoding="utf-8"))
    OUTPUT.write_text(build_html(title, sections), encoding="utf-8")
    sentence_count = sum(len(section.sentences) for section in sections)
    print(f"Wrote {OUTPUT} with {sentence_count} sentence prompts.")


if __name__ == "__main__":
    main()
