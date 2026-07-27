#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py
SciBot Platform: a self-contained web app for uploading scientific PDFs and running
classify / rank / summarize bots against them, powered by Claude.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

import db
import pdf_utils
import config as cfg
from llm_bots import LLMClient, ClassifyBot, CompareBot, SummarizeBot, DEFAULT_CATEGORIES

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.secret_key = "dev-key-change-me"  # only matters for flash messages
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB per upload

db.init_db()
settings = cfg.load_config()


def get_llm_client():
    if not settings.get("anthropic_api_key"):
        return None
    return LLMClient(api_key=settings["anthropic_api_key"], model=settings.get("model", "claude-sonnet-4-5"))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Routes: core pages
##################################################

@app.route("/")
def index():
    documents = db.get_documents()
    has_key = bool(settings.get("anthropic_api_key"))
    return render_template("index.html", documents=documents, has_key=has_key)


@app.route("/upload", methods=["POST"])
def upload():
    if "pdf_file" not in request.files:
        flash("No file selected.")
        return redirect(url_for("index"))

    files = request.files.getlist("pdf_file")
    added = 0
    for file in files:
        if file.filename == "":
            continue
        if not allowed_file(file.filename):
            flash(f"Skipped {file.filename}: not a PDF.")
            continue

        filename = secure_filename(file.filename)
        save_path = UPLOAD_DIR / filename
        file.save(save_path)

        text_content = pdf_utils.extract_text(save_path)
        title = pdf_utils.guess_title(text_content, fallback=filename)

        db.add_document(filename, save_path, title, text_content)
        added += 1

    flash(f"Uploaded {added} document(s).")
    return redirect(url_for("index"))


@app.route("/document/<int:doc_id>")
def document_detail(doc_id):
    doc = db.get_document(doc_id)
    if not doc:
        flash("Document not found.")
        return redirect(url_for("index"))

    classification = db.get_classification(doc_id)
    summary = db.get_summary(doc_id)
    return render_template("document.html", doc=doc, classification=classification, summary=summary)


@app.route("/document/<int:doc_id>/delete", methods=["POST"])
def document_delete(doc_id):
    db.delete_document(doc_id)
    flash("Document deleted.")
    return redirect(url_for("index"))


# Routes: bot actions
##################################################

@app.route("/document/<int:doc_id>/classify", methods=["POST"])
def classify(doc_id):
    llm = get_llm_client()
    if llm is None:
        flash("No Anthropic API key configured. See config.example.json / README.")
        return redirect(url_for("document_detail", doc_id=doc_id))

    doc = db.get_document(doc_id)
    bot = ClassifyBot(llm, categories=DEFAULT_CATEGORIES)
    response, category = bot.query(doc["text_content"])
    db.add_classification(doc_id, category, response)

    flash(f"Classified as: {category}")
    return redirect(url_for("document_detail", doc_id=doc_id))


@app.route("/document/<int:doc_id>/summarize", methods=["POST"])
def summarize(doc_id):
    llm = get_llm_client()
    if llm is None:
        flash("No Anthropic API key configured. See config.example.json / README.")
        return redirect(url_for("document_detail", doc_id=doc_id))

    doc = db.get_document(doc_id)
    bot = SummarizeBot(llm)
    summary = bot.summarize(doc["text_content"], doc_name=doc["title"])
    db.add_summary(doc_id, summary)

    flash("Summary generated.")
    return redirect(url_for("document_detail", doc_id=doc_id))


@app.route("/compare", methods=["GET", "POST"])
def compare():
    documents = db.get_documents()

    if request.method == "POST":
        llm = get_llm_client()
        if llm is None:
            flash("No Anthropic API key configured. See config.example.json / README.")
            return redirect(url_for("compare"))

        doc_id_a = int(request.form["doc_id_a"])
        doc_id_b = int(request.form["doc_id_b"])
        if doc_id_a == doc_id_b:
            flash("Choose two different documents.")
            return redirect(url_for("compare"))

        doc_a = db.get_document(doc_id_a)
        doc_b = db.get_document(doc_id_b)

        bot = CompareBot(llm)
        response, winner = bot.query(doc_a["text_content"], doc_b["text_content"])
        db.add_pairwise_score(doc_id_a, doc_id_b, winner, response)

        winner_title = doc_a["title"] if winner == "A" else doc_b["title"] if winner == "B" else "Unclear"
        flash(f"Result: {winner_title}")
        return redirect(url_for("compare"))

    rankings = db.get_rankings()
    history = db.get_pairwise_scores()
    return render_template("compare.html", documents=documents, rankings=rankings, history=history)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
