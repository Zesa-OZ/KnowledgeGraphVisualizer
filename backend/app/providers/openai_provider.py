from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI

from .base import Triples


class Triple(BaseModel):
    source: str = Field(..., min_length=1)
    relation: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)


class TripleExtraction(BaseModel):
    triples: List[Triple]


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract_triples(self, text: str) -> Triples:
        system = """
        You extract a compact, visually connected knowledge graph from text.

        Rules:
        - First, identify 1 to 3 CENTRAL HUB entities (organizations, concepts or people).
        - ALL triples must connect to at least one of these hubs.
        - Output between 12 and 22 triples total.
        - Reuse entity names exactly (no synonyms, no abbreviations).
        - Avoid generic entities unless they are hubs.
        - Relations must be short verb phrases (2-6 words), in Spanish if the input is Spanish.
        - Do NOT invent facts.
        - The goal is a single connected graph suitable for visualization.
        """
        user = f"""
        Text:
        \"\"\"{text}\"\"\"

        Extract a compact connected graph following the rules.
        """

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            text_format=TripleExtraction,
            # para controlar coste un poco:
            max_output_tokens=600,
        )

        parsed: TripleExtraction = response.output_parsed

        def norm(s: str) -> str:
            return " ".join((s or "").strip().split())

        bad = {"esto", "esta", "este", "esa", "ese", "ello", "él", "ella", "ellos", "ellas", "it", "this", "that"}

        clean = []
        seen = set()

        for t in parsed.triples:
            s = norm(t.source)
            r = norm(t.relation)
            o = norm(t.target)

            if not s or not r or not o:
                continue
            if s.lower() in bad or o.lower() in bad:
                continue
            if len(s) < 3 or len(o) < 3:
                continue

            key = (s.lower(), r.lower(), o.lower())
            if key in seen:
                continue
            seen.add(key)

            clean.append({"source": s, "relation": r, "target": o})

        return clean

