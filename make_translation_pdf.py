#!/usr/bin/env python3
"""Generate a line-by-line English interpretation worksheet PDF from content.md.

The script intentionally uses only Python's standard library so the PDF can be
rebuilt in restricted environments without installing extra packages.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

SOURCE = Path("content.md")
OUTPUT = Path("content_line_by_line_translation.pdf")
PAGE_WIDTH = 595  # A4 width in points
PAGE_HEIGHT = 842  # A4 height in points
MARGIN_X = 48
MARGIN_TOP = 54
MARGIN_BOTTOM = 54
BODY_SIZE = 10.5
SMALL_SIZE = 8.5
TITLE_SIZE = 17
LINE_HEIGHT = 14
BLANK_LINE_GAP = 16

SECTION_TITLES = {
    "동물 의식과 ‘the ghost’": "Animal consciousness and 'the ghost'",
    "자동차 디자인과 ‘얼굴’": "Automobile design and 'faces'",
    "동물 크기와 시간": "Animal size and time",
    "관광 산업의 변화": "Changes in the tourism industry",
    "교통수단 비율 설명": "Description of transportation percentages",
    "언어철학자 Paul Grice": "Philosopher of language Paul Grice",
    "Green Dewywood Drawing Competition": "Green Dewywood Drawing Competition",
    "Summer Night Drone Event": "Summer Night Drone Event",
    "예술가의 자기 검열": "Artists' self-censorship",
    "고대 그리스식 교육": "Ancient Greek-style education",
    "과학자의 발견과 실용성": "Scientific discovery and practicality",
    "인구 조사와 도시 거버넌스": "Population records and urban governance",
    "원거리 식품의 환경 영향": "Environmental impact of long-distance food",
    "생태계 안정성과 종 다양성": "Ecosystem stability and species diversity",
    "라이브 음악의 가치": "The value of live music",
    "비둘기 구조 이야기": "A pigeon rescue story",
    "2점 문항 지문": "Two-point question passages",
}


def normalize_text(text: str) -> str:
    """Convert markdown/source typography to PDF-safe Latin text."""
    replacements = {
        "\u00a0": " ",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "%": " percent",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"【[^】]+】", "", text)
    return " ".join(text.split())


def section_title(raw_title: str) -> str:
    """Use English section labels because the dependency-free PDF uses Helvetica."""
    cleaned = raw_title.replace(" ", " ").strip()
    question = ""
    match = re.search(r"\(([^)]+)\)", cleaned)
    if match:
        question = match.group(1).replace("문항", "Question").strip()
        cleaned = cleaned[: match.start()].strip()
    english = SECTION_TITLES.get(cleaned, normalize_text(cleaned))
    return f"{english} ({question})" if question else english


@dataclass
class Section:
    title: str
    sentences: list[str]


def parse_content(markdown: str) -> tuple[str, list[Section]]:
    title = "Line-by-Line English Interpretation Worksheet"
    sections: list[Section] = []
    current: Section | None = None

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            title = "2027 June Mock Exam English - Reading Sentences"
        elif line.startswith("## "):
            current = Section(section_title(line[3:]), [])
            sections.append(current)
        elif line.startswith("- ") and current is not None:
            current.sentences.append(normalize_text(line[2:]))
    return title, sections


def pdf_escape(text: str) -> bytes:
    safe = text.encode("cp1252", errors="replace")
    safe = safe.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    return safe


def wrap_text(text: str, size: float, max_width: float) -> list[str]:
    chars = max(24, int(max_width / (size * 0.49)))
    wrapped: list[str] = []
    for paragraph in text.split("\n"):
        wrapped.extend(textwrap.wrap(paragraph, width=chars, break_long_words=False) or [""])
    return wrapped


class SimplePDF:
    def __init__(self) -> None:
        self.pages: list[list[bytes]] = []
        self.current: list[bytes] = []
        self.y = PAGE_HEIGHT - MARGIN_TOP
        self.page_number = 0
        self.new_page()

    def new_page(self) -> None:
        if self.current:
            self.footer()
            self.pages.append(self.current)
        self.page_number += 1
        self.current = []
        self.y = PAGE_HEIGHT - MARGIN_TOP
        self.text(f"Page {self.page_number}", PAGE_WIDTH - MARGIN_X - 42, 24, SMALL_SIZE, font="F1")

    def footer(self) -> None:
        self.line(MARGIN_X, 36, PAGE_WIDTH - MARGIN_X, 36, 0.4)

    def ensure_space(self, needed: float) -> None:
        if self.y - needed < MARGIN_BOTTOM:
            self.new_page()

    def text(self, text: str, x: float, y: float, size: float, font: str = "F1") -> None:
        self.current.append(
            b"BT /%s %.2f Tf 1 0 0 1 %.2f %.2f Tm (%s) Tj ET\n"
            % (font.encode(), size, x, y, pdf_escape(text))
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, width: float = 0.5) -> None:
        self.current.append(b"%.2f w %.2f %.2f m %.2f %.2f l S\n" % (width, x1, y1, x2, y2))

    def add_wrapped(self, text: str, size: float = BODY_SIZE, font: str = "F1", indent: float = 0) -> None:
        max_width = PAGE_WIDTH - (MARGIN_X * 2) - indent
        lines = wrap_text(text, size, max_width)
        self.ensure_space(len(lines) * LINE_HEIGHT + 4)
        for line in lines:
            self.text(line, MARGIN_X + indent, self.y, size, font=font)
            self.y -= LINE_HEIGHT

    def add_heading(self, text: str) -> None:
        self.ensure_space(36)
        self.y -= 7
        self.add_wrapped(text, 12.5, font="F2")
        self.y -= 3

    def add_sentence(self, index: int, sentence: str) -> None:
        wrapped = wrap_text(f"{index}. {sentence}", BODY_SIZE, PAGE_WIDTH - (MARGIN_X * 2))
        needed = len(wrapped) * LINE_HEIGHT + 50
        self.ensure_space(needed)
        for line in wrapped:
            self.text(line, MARGIN_X, self.y, BODY_SIZE, font="F1")
            self.y -= LINE_HEIGHT
        self.text("Korean interpretation:", MARGIN_X + 14, self.y - 1, SMALL_SIZE, font="F2")
        self.y -= BLANK_LINE_GAP
        self.line(MARGIN_X + 14, self.y, PAGE_WIDTH - MARGIN_X, self.y)
        self.y -= 18
        self.line(MARGIN_X + 14, self.y, PAGE_WIDTH - MARGIN_X, self.y)
        self.y -= 12

    def finish(self) -> bytes:
        if self.current:
            self.footer()
            self.pages.append(self.current)
            self.current = []
        objects: list[bytes] = []
        catalog_id = 1
        pages_id = 2
        font_regular_id = 3
        font_bold_id = 4
        next_id = 5
        page_ids: list[int] = []
        content_ids: list[int] = []
        for _ in self.pages:
            page_ids.append(next_id)
            content_ids.append(next_id + 1)
            next_id += 2

        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        kids = b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
        objects.append(b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_ids)).encode() + b" >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        for page_id, content_id, commands in zip(page_ids, content_ids, self.pages):
            page_obj = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode()
            stream = b"".join(commands)
            content_obj = b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"endstream"
            objects.append(page_obj)
            objects.append(content_obj)

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for number, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{number} 0 obj\n".encode())
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")
        xref_start = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode())
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
        )
        return bytes(pdf)


def main() -> None:
    title, sections = parse_content(SOURCE.read_text(encoding="utf-8"))
    pdf = SimplePDF()
    pdf.add_wrapped(title, TITLE_SIZE, font="F2")
    pdf.y -= 4
    pdf.add_wrapped(
        "Use each numbered English sentence to write your own Korean interpretation on the two ruled lines below it.",
        BODY_SIZE,
    )
    pdf.y -= 8

    sentence_number = 1
    for section in sections:
        pdf.add_heading(section.title)
        for sentence in section.sentences:
            pdf.add_sentence(sentence_number, sentence)
            sentence_number += 1

    OUTPUT.write_bytes(pdf.finish())
    print(f"Wrote {OUTPUT} with {sentence_number - 1} sentence prompts.")


if __name__ == "__main__":
    main()
