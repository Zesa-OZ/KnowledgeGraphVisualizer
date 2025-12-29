import { useMemo, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
    const [text, setText] = useState("Microsoft invirtió en OpenAI. OpenAI creó GPT-4.");
    const [provider, setProvider] = useState("openai");
    const [usedProvider, setUsedProvider] = useState("");
    const [graph, setGraph] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [url, setUrl] = useState("");
    const [extracting, setExtracting] = useState(false);
    const [highlight, setHighlight] = useState({ nodes: new Set(), links: new Set() });

    const fetchGraph = async () => {
        setLoading(true);
        setError("");
        try {
            const res = await fetch(`${API_BASE}/analyze?provider=${encodeURIComponent(provider)}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text }),
            });

            if (!res.ok) {
                const msg = await res.text();
                throw new Error(`${res.status} ${res.statusText} - ${msg}`);
            }

            const data = await res.json();
            setGraph(data);
            setUsedProvider(data.provider || "");
        } catch (e) {
            setError(e?.message || "Error desconocido");
        } finally {
            setLoading(false);
        }
    };

    const extractFromUrl = async () => {
        setExtracting(true);
        setError("");
        try {
            const res = await fetch(`${API_BASE}/extract`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url }),
            });

            if (!res.ok) {
                const msg = await res.text();
                throw new Error(`${res.status} ${res.statusText} - ${msg}`);
            }

            const data = await res.json();
            setText(data.text || "");
        } catch (e) {
            setError(e?.message || "Error extrayendo URL");
        } finally {
            setExtracting(false);
        }
    };

    const analyzeUrl = async () => {
        await extractFromUrl();
        // Ojo: setText es async; para no depender del estado,
        // repetimos extract aquí y analizamos directamente con el texto resultante.
        // (simple y fiable)
        setLoading(true);
        setError("");
        try {
            const resExtract = await fetch(`${API_BASE}/extract`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url }),
            });

            if (!resExtract.ok) {
                const msg = await resExtract.text();
                throw new Error(`${resExtract.status} ${resExtract.statusText} - ${msg}`);
            }

            const ex = await resExtract.json();
            const extractedText = ex.text || "";
            setText(extractedText);

            const resAnalyze = await fetch(
                `${API_BASE}/analyze?provider=${encodeURIComponent(provider)}`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: extractedText }),
                }
            );

            if (!resAnalyze.ok) {
                const msg = await resAnalyze.text();
                throw new Error(`${resAnalyze.status} ${resAnalyze.statusText} - ${msg}`);
            }

            const data = await resAnalyze.json();
            setGraph(data);
            setUsedProvider(data.provider || "");
        } catch (e) {
            setError(e?.message || "Error analizando URL");
        } finally {
            setLoading(false);
        }
    };

    const buildHighlights = (node) => {
        const hn = new Set([node.id]);
        const hl = new Set();

        graph.links.forEach((l) => {
            const s = typeof l.source === "object" ? l.source.id : l.source;
            const t = typeof l.target === "object" ? l.target.id : l.target;
            if (s === node.id || t === node.id) {
                hl.add(l);
                hn.add(s);
                hn.add(t);
            }
        });

        setHighlight({ nodes: hn, links: hl });
    };

    const graphData = useMemo(() => graph, [graph]);

    return (
        <div style={{ height: "100vh", padding: 16, boxSizing: "border-box" }}>
            <div
                style={{
                    height: "100%",
                    display: "grid",
                    gridTemplateColumns: "420px 1fr",
                    borderRadius: 18,
                    overflow: "hidden",
                    border: "1px solid rgba(255,255,255,0.08)",
                    boxShadow: "0 20px 60px rgba(0,0,0,0.45)",
                    background: "rgba(0,0,0,0.12)",
                }}
            >
                <div
                    style={{
                        padding: 16,
                        overflow: "auto",
                        borderRight: "1px solid rgba(255,255,255,0.08)",
                        background:
                            "linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02))",
                        gap: 12,
                        display: "flex",
                        flexDirection: "column",
                    }}
                >
                    <h2 style={{ marginTop: 0 }}>Knowledge Graph Visualizer</h2>
                    <p style={{ marginTop: 0, opacity: 0.7 }}>
                        Pega texto → analizar → grafo interactivo
                    </p>

                    <div
                        style={{
                            marginTop: 12,
                            padding: 12,
                            borderRadius: 14,
                            border: "1px solid rgba(255,255,255,0.08)",
                            background: "rgba(0,0,0,0.25)",
                        }}
                    >
                        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 10 }}>
                            <label style={{ fontSize: 13, opacity: 0.8 }}>Proveedor</label>
                            <select
                                value={provider}
                                onChange={(e) => setProvider(e.target.value)}
                            >
                                <option value="openai">OpenAI</option>
                                <option value="ollama">Ollama</option>
                            </select>
                        </div>

                        <div style={{ marginBottom: 10 }}>
                            <label style={{ fontSize: 13, opacity: 0.8 }}>URL (opcional)</label>
                            <input
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://..."
                                style={{ marginTop: 6 }}
                            />
                            <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
                                <button
                                    onClick={extractFromUrl}
                                    disabled={!url || extracting}
                                >
                                    {extracting ? "Extrayendo..." : "Extraer URL → Texto"}
                                </button>

                                <button
                                    onClick={analyzeUrl}
                                    disabled={!url || loading || extracting}
                                >
                                    {loading ? "Analizando..." : "Analizar URL → Grafo"}
                                </button>
                            </div>
                        </div>

                        <textarea
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            rows={10}
                        />

                        <button
                            onClick={fetchGraph}
                            disabled={loading}
                        >
                            {loading ? "Analizando..." : "Analizar y dibujar grafo"}
                        </button>

                        {usedProvider && (
                            <div style={{ marginTop: 10, fontSize: 12, opacity: 0.8 }}>
                                Provider usado: <b>{usedProvider}</b>
                            </div>
                        )}

                        {error && (
                            <div style={{ marginTop: 12, padding: 10, border: "1px solid #f3c0c0" }}>
                                <b>Error:</b> {error}
                            </div>
                        )}

                        <div style={{ marginTop: 12, fontSize: 12, opacity: 0.7 }}>
                            Backend: {API_BASE}
                        </div>
                    </div>
                </div>

                <div style={{ position: "relative", background: "radial-gradient(900px 600px at 50% 40%, rgba(255,255,255,0.06), transparent 60%)", boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.06)", overflow: "hidden" }}>
                    <ForceGraph2D
                        graphData={graphData}
                        nodeLabel={(n) => n.id}
                        linkLabel={(l) => l.relation}
                        linkDirectionalArrowLength={6}
                        linkDirectionalArrowRelPos={1}
                        linkCurvature={0.15}
                        linkDirectionalParticles={2}
                        linkDirectionalParticleWidth={2}
                        linkDirectionalParticleSpeed={0.006}
                        nodeRelSize={6}
                        onNodeClick={(node) => buildHighlights(node)}
                        onBackgroundClick={() => setHighlight({ nodes: new Set(), links: new Set() })}
                        linkColor={(l) =>
                            highlight.links.has(l) ? "#60a5fa" : "rgba(148,163,184,0.25)"
                        }
                        linkWidth={(l) => (highlight.links.has(l) ? 2 : 1)}
                        nodeCanvasObject={(node, ctx, globalScale) => {
                            const fontSize = 12 / globalScale;
                            const isOn = highlight.nodes.has(node.id);

                            ctx.beginPath();
                            ctx.arc(node.x, node.y, isOn ? 7 : 5, 0, 2 * Math.PI);
                            ctx.fillStyle = isOn ? "#60a5fa" : "#94a3b8";
                            ctx.fill();

                            if (isOn) {
                                ctx.font = `${fontSize}px sans-serif`;
                                ctx.fillStyle = "#e5e7eb";
                                ctx.fillText(node.id, node.x + 10, node.y + 3);
                            }
                        }}
                    />
                </div>
            </div>
        </div>
    );

}
