from __future__ import annotations

import json
import re
from typing import Any

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError

from .base import Triples


class Triple(BaseModel):
    source: str = Field(..., min_length=1)
    relation: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)


class TripleExtraction(BaseModel):
    triples: list[Triple]


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    # Quita ```json ... ``` o ``` ... ```
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str, model: str):
        self.base_url = (base_url or "").rstrip("/")
        self.model = model or "llama3.1"

    def extract_triples(self, text: str) -> Triples:
        # 1) Comprobar que Ollama está vivo (rápido)
        try:
            with httpx.Client(timeout=3) as client:
                r = client.get(f"{self.base_url}/api/tags")
                r.raise_for_status()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Ollama no está disponible. Instálalo y arráncalo "
                    f"(esperado en {self.base_url})."
                ),
            )

        system = """
        You extract a compact, visually connected knowledge graph from text.

        Return ONLY valid JSON matching this schema:
        {
        "triples": [
            {"source": "...", "relation": "...", "target": "..."}
        ]
        }

        Rules:
        - Output between 12 and 22 triples.
        - Prefer 1-3 hub entities and connect everything to them.
        - Reuse entity strings consistently.
        - Relations must be short verb phrases (2-6 words), in Spanish if input is Spanish.
        - Do NOT invent facts.
        """

        user = f"""
        Text:
        \"\"\"{text}\"\"\"

        Return JSON only.
        """

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system.strip()},
                {"role": "user", "content": user.strip()},
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        # 2) Llamada real a /api/chat
        try:
            with httpx.Client(timeout=60) as client:
                r = client.post(f"{self.base_url}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"Ollama error: {e}")

        content = (
            (data.get("message") or {}).get("content")
            if isinstance(data, dict)
            else None
        )

        if not content or not isinstance(content, str):
            raise HTTPException(status_code=400, detail="Ollama returned empty response.")

        # 3) Parsear JSON y validar con Pydantic
        raw = _strip_code_fences(content)

        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            # Si Ollama devuelve texto alrededor, intentamos extraer primer bloque JSON
            m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if not m:
                raise HTTPException(status_code=400, detail="Ollama did not return valid JSON.")
            obj = json.loads(m.group(0))

        try:
            parsed = TripleExtraction.model_validate(obj)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Ollama JSON schema invalid: {e}")

        return [
            {
                "source": t.source.strip(),
                "relation": t.relation.strip(),
                "target": t.target.strip(),
            }
            for t in parsed.triples
        ]
