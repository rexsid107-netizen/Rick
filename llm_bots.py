#!/usr/bin/env python3
# -*-             "analysis, then finish your reply with a line that strictly follows this format: "
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
