from __future__ import annotations
from typing import Protocol, List, Dict

Triples = List[Dict[str, str]]

class GraphProvider(Protocol):
    name: str
    def extract_triples(self, text: str) -> Triples: ...
