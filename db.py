#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db.py
Simple SQLite-backed storage for documents, classifications, rankings, and summaries.
This replaces the original MySQL-based DocumentDatabase with a zero-setup alternative.
"""

import sqlite3
import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "scibot.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        title TEXT,
        len_chars INTEGER,
        text_content TEXT,
        datetime_added TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS classifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER NOT NULL,
        category TEXT,
        full_response TEXT,
        datetime_added TEXT NOT NULL,
        FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER NOT NULL,
        summary TEXT,
        datetime_added TEXT NOT NULL,
        FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores_pairwise (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id_a INTEGER NOT NULL,
        doc_id_b INTEGER NOT NULL,
        winner TEXT,
        full_response TEXT,
        datetime_added TEXT NOT NULL,
        FOREIGN KEY (doc_id_a) REFERENCES documents(doc_id),
        FOREIGN KEY (doc_id_b) REFERENCES documents(doc_id)
    )
    """)

    conn.commit()
    conn.close()


def add_document(file_name, file_path, title, text_content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO documents (file_name, file_path, title, len_chars, text_content, datetime_added)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (file_name, str(file_path), title, len(text_content), text_content,
         datetime.datetime.now().isoformat())
    )
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    return doc_id


def get_documents():
    conn = get_connection()
    rows = conn.execute("SELECT doc_id, file_name, title, len_chars, datetime_added FROM documents ORDER BY doc_id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document(doc_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_document(doc_id):
    conn = get_connection()
    # Delete dependent rows first to satisfy the foreign key constraints.
    conn.execute("DELETE FROM classifications WHERE doc_id=?", (doc_id,))
    conn.execute("DELETE FROM summaries WHERE doc_id=?", (doc_id,))
    conn.execute("DELETE FROM scores_pairwise WHERE doc_id_a=? OR doc_id_b=?", (doc_id, doc_id))
    conn.execute("DELETE FROM documents WHERE doc_id=?", (doc_id,))
    conn.commit()
    conn.close()


def add_classification(doc_id, category, full_response):
    conn = get_connection()
    conn.execute(
        "INSERT INTO classifications (doc_id, category, full_response, datetime_added) VALUES (?, ?, ?, ?)",
        (doc_id, category, full_response, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_classification(doc_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM classifications WHERE doc_id=? ORDER BY id DESC LIMIT 1", (doc_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_summary(doc_id, summary):
    conn = get_connection()
    conn.execute(
        "INSERT INTO summaries (doc_id, summary, datetime_added) VALUES (?, ?, ?)",
        (doc_id, summary, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_summary(doc_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM summaries WHERE doc_id=? ORDER BY id DESC LIMIT 1", (doc_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_pairwise_score(doc_id_a, doc_id_b, winner, full_response):
    conn = get_connection()
    conn.execute(
        """INSERT INTO scores_pairwise (doc_id_a, doc_id_b, winner, full_response, datetime_added)
           VALUES (?, ?, ?, ?, ?)""",
        (doc_id_a, doc_id_b, winner, full_response, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_pairwise_scores():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM scores_pairwise ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_rankings():
    """Compute a simple win-count ranking from pairwise comparisons."""
    conn = get_connection()
    docs = {d["doc_id"]: {"doc_id": d["doc_id"], "title": d["title"] or d["file_name"],
                           "wins": 0, "losses": 0, "ties": 0}
            for d in get_documents()}
    conn.close()

    for match in get_pairwise_scores():
        a, b, winner = match["doc_id_a"], match["doc_id_b"], match["winner"]
        if a not in docs or b not in docs:
            continue
        if winner == "A":
            docs[a]["wins"] += 1
            docs[b]["losses"] += 1
        elif winner == "B":
            docs[b]["wins"] += 1
            docs[a]["losses"] += 1
        else:
            docs[a]["ties"] += 1
            docs[b]["ties"] += 1

    ranking = sorted(docs.values(), key=lambda d: (-d["wins"], d["losses"]))
    return ranking
