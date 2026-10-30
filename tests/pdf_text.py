"""Readable text for a reportlab PDF, so a test can compare and diff what the pages draw."""

import base64
import re
import zlib


def pdf_text(pdf: bytes) -> str:
    """The PDF's title, page sizes and each page's drawing commands, as text.

    reportlab writes each page as an ASCII85 and Flate encoded stream. Decoded, a line says
    what is drawn where, such as ``BT 1 0 0 1 54 738 Tm (Arithmetic) Tj T* ET``, so a changed
    title or a moved line is a changed line. Fonts are named, not embedded, in these PDFs.
    """
    title = re.search(rb"/Title \(((?:\\.|[^\\)])*)\)", pdf)
    boxes = re.findall(rb"/MediaBox \[ ([\d. ]+) \]", pdf)
    lines = [
        f"title: {title.group(1).decode('latin-1') if title else ''}",
        "media boxes: " + "; ".join(box.decode("ascii") for box in boxes),
    ]
    for number, raw in enumerate(re.findall(rb"stream\n(.*?)endstream", pdf, re.DOTALL), start=1):
        content = zlib.decompress(base64.a85decode(raw.strip().removesuffix(b"~>")))
        lines.append(f"--- stream {number}")
        lines.append(content.decode("latin-1").strip())
    return "\n".join(lines)
