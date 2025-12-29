from __future__ import annotations

import re
import httpx
from bs4 import BeautifulSoup
from readability import Document


def _normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_text_from_url(url: str, timeout_seconds: int = 20) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (KnowledgeGraphVisualizer/1.0)"
    }

    with httpx.Client(timeout=timeout_seconds, follow_redirects=True, headers=headers) as client:
        r = client.get(url)
        r.raise_for_status()
        html = r.text

    # 1) Readability: intenta sacar el “contenido principal”
    doc = Document(html)
    main_html = doc.summary(html_partial=True)

    # 2) Soup: limpiar tags
    soup = BeautifulSoup(main_html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = _normalize_text(text)

    # fallback si readability saca poco
    if len(text) < 400:
        soup2 = BeautifulSoup(html, "lxml")
        for tag in soup2(["script", "style", "noscript"]):
            tag.decompose()
        text2 = soup2.get_text(separator=" ", strip=True)
        text2 = _normalize_text(text2)
        if len(text2) > len(text):
            text = text2

    return text
