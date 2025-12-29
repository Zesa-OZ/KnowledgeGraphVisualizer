from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from app.providers import get_provider
from app.budget_guard import BudgetGuard
from fastapi import FastAPI, Query
from fastapi import HTTPException
from app.url_extract import extract_text_from_url


class Settings(BaseSettings):
    app_env: str = "dev"
    ai_provider: str = "openai"
    monthly_budget_usd: float = 5.0
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    budget_enforce: bool = True
    budget_cache_seconds: int = 600
    openai_admin_key: str = ""
    openai_project_id: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    frontend_origin: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()

budget_guard = BudgetGuard(
    admin_key=settings.openai_admin_key,
    project_id=settings.openai_project_id,
    budget_usd=settings.monthly_budget_usd,
    cache_seconds=settings.budget_cache_seconds,
)

app = FastAPI(title="Knowledge Graph Visualizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    text: str

class ExtractRequest(BaseModel):
    url: str

@app.get("/health")
def health():
    return {
        "ok": True,
        "env": settings.app_env,
        "provider": settings.ai_provider,
        "budget": settings.monthly_budget_usd,
    }

@app.post("/analyze")
def analyze(req: AnalyzeRequest, provider: str = Query(default="")):
    effective_provider = provider.strip().lower() or settings.ai_provider
    provider_impl = get_provider(effective_provider, settings)

    status = None
    if effective_provider == "openai" and settings.budget_enforce:
        status = budget_guard.enforce_or_raise()

    triples = provider_impl.extract_triples(req.text)

    nodes_set = set()
    links = []

    for t in triples:
        s = (t.get("source") or "").strip()
        r = (t.get("relation") or "").strip()
        tgt = (t.get("target") or "").strip()
        if not s or not r or not tgt:
            continue

        nodes_set.add(s)
        nodes_set.add(tgt)
        links.append({"source": s, "target": tgt, "relation": r})

    nodes = [{"id": n} for n in sorted(nodes_set)]
    result = {"nodes": nodes, "links": links, "provider": provider_impl.name}

    if status is not None:
        result["budget"] = {
            "month": status.month_key,
            "spent_usd": status.spent_usd,
            "budget_usd": status.budget_usd,
            "hard_cap_active": status.hard_cap_active,
        }

    degree = {}
    for l in links:
        degree[l["source"]] = degree.get(l["source"], 0) + 1
        degree[l["target"]] = degree.get(l["target"], 0) + 1

    # Hub principal = nodo con mayor grado
    if degree:
        main_hub = max(degree.items(), key=lambda x: x[1])[0]
    else:
        main_hub = None

    # Mantener enlaces conectados directa o indirectamente al hub
    if main_hub:
        connected = {main_hub}
        changed = True

        # BFS simple para encontrar nodos conectados al hub
        while changed:
            changed = False
            for l in links:
                if l["source"] in connected and l["target"] not in connected:
                    connected.add(l["target"])
                    changed = True
                if l["target"] in connected and l["source"] not in connected:
                    connected.add(l["source"])
                    changed = True

        links = [l for l in links if l["source"] in connected and l["target"] in connected]
        nodes = [{"id": n} for n in sorted(connected)]
    return result

@app.post("/extract")
def extract(req: ExtractRequest):
    url = (req.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    try:
        text = extract_text_from_url(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not extract url: {e}")

    # devolvemos solo los primeros chars para no petar el front
    return {
        "url": url,
        "length": len(text),
        "text": text,
    }
