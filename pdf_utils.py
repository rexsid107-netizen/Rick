#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_utils.py
Plain-text extraction from PDFs (replaces the original GROBID/TEI-XML ingestion pipeline,
which required a running GROBID service). This is less structured (no clean title/author
parsing) but requires zero extra infrastructure.
"""

from pypdf import PdfReader


def extract_text(file_path):
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        try:
            text_parts.append(page.extract_text() or "")
        except Exception:
            pass
    return "\n".join(text_parts)


def guess_title(text, fallback):
    """Very rough heuristic: use the first non-empty line of reasonable length as a title guess."""
    for line in text.splitlines():
        line = line.strip()
        if 8 < len(line) < 200:
            return line
    return fallback
