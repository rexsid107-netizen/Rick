#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_bots.py
Classify / Compare / Summarize bots, adapted from the uploaded tool_bots.py and bots.py.
Ported to the current Anthropic Messages API (client.messages.create), since the original
code used the deprecated client.completion()/HUMAN_PROMPT style.

Categories are configurable in config.py.
"""

import re
import anthropic

DEFAULT_CATEGORIES = """self-assembly: Publications related to self-assembling materials (block copolymer thin films, nanoparticle superlattices, DNA self-assembly, etc.)

machine-learning: Papers related to AI, machine learning, data analytics, or autonomous experimentation.

scattering: Method/technique development for x-ray or neutron scattering (SAXS, WAXS, GISAXS, GIWAXS, reflectivity, etc.)

materials: General materials-science studies not fitting the above (photovoltaics, battery materials, membranes, etc.)

other: Anything that does not fit the above categories."""


class LLMClient:
    """Thin wrapper around the Anthropic Messages API."""

    def __init__(self, api_key, model="claude-sonnet-4-5", max_tokens=1200):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def chat(self, system, user_content):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class ClassifyBot:
    """Puts a document into one of the specified categories."""

    def __init__(self, llm: LLMClient, categories=DEFAULT_CATEGORIES, char_limit=16000):
        self.llm = llm
        self.categories = categories
        self.char_limit = char_limit
        self.instruction = (
            "Analyze the text below, taken from a scientific publication. Identify the most "
            "appropriate category for this publication from the list provided. Give a brief "
            "analysis, then finish your reply with a line that strictly follows this format: "
            '"The publication should be in category: CATEGORY" (where CATEGORY is one of the '
            f"ones listed below).\n\nValid categories:\n{categories}"
        )
        self.answer_re = re.compile(r"should be in category:?\s*([a-zA-Z\- ]+)", re.IGNORECASE)

    def query(self, text):
        text = text[: self.char_limit]
        response = self.llm.chat(self.instruction, f"Publication text:\n\n{text}")
        m = self.answer_re.search(response)
        category = m.group(1).strip() if m else "?"
        return response, category


class CompareBot:
    """Compares two documents and decides which is more likely to be high-impact."""

    def __init__(self, llm: LLMClient, char_limit_each=8000):
        self.llm = llm
        self.char_limit_each = char_limit_each
        self.instruction = (
            "Analyze the two extracts below, from PUBLICATION_A and PUBLICATION_B (scientific "
            "publications). Decide which is more likely to be \"high impact\" (influential, drives "
            "follow-on work, changes perspectives in the field). Give a brief impact analysis of "
            "each, compare them, then finish with a line strictly following this format: "
            '"The higher-impact publication is: PUBLICATION_X" (X is A or B).'
        )
        self.answer_re = re.compile(r"higher-impact publication is:?\s*PUBLICATION_([AB])", re.IGNORECASE)

    def query(self, text_a, text_b):
        text_a = text_a[: self.char_limit_each]
        text_b = text_b[: self.char_limit_each]
        content = f"PUBLICATION_A:\n\n{text_a}\n\nPUBLICATION_B:\n\n{text_b}\n"
        response = self.llm.chat(self.instruction, content)
        m = self.answer_re.search(response)
        winner = m.group(1) if m else "?"
        return response, winner


class SummarizeBot:
    """Summarizes a scientific text concisely."""

    def __init__(self, llm: LLMClient, char_limit=16000):
        self.llm = llm
        self.char_limit = char_limit
        self.instruction = (
            "Your task is to take text from scientific journal articles and summarize it "
            "concisely. Capture as much information as possible while avoiding repetition. "
            "Omit details very specific to the particular paper. Emphasize generalizable "
            "insights. Do not make things up."
        )

    def summarize(self, text, doc_name="<UNKNOWN>"):
        text = text[: self.char_limit]
        request = f"Summarize this (from the paper {doc_name}):\n\n{text}"
        return self.llm.chat(self.instruction, request)
