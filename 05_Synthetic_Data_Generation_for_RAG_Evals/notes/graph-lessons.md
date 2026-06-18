# Graphs: Lessons Learned (Session 5 / Ragas Context)

Notes from working through Task 3 and unpacking why "graph" keeps showing up everywhere.

---

## 1. "Graph" is overloaded — same word, different jobs

| What people call a "graph" | Nodes are… | Edges mean… |
|---|---|---|
| **Ragas `KnowledgeGraph`** | PDF page chunks | "These pages are related enough to combine" |
| **LangGraph** | Agent steps / states | "What runs next" |
| **Vector retrieval** (implicit) | Embedded chunks | "Semantically similar" (often not stored as explicit edges) |
| **Knowledge graph** (Neo4j, Wikidata) | Formal entities | Typed facts (`Cat → isA → Mammal`) |
| **Neural net** | Neurons / ops | Weights / data flow |

Same primitive — **things + relationships** — different implementations for different questions.

---

## 2. Ragas's graph: a purpose-built Python structure

**Not LangGraph. Not a graph DB. Not NetworkX.**

```text
KnowledgeGraph          ← Ragas dataclass (plain Python)
├── nodes: list[Node]   ← one per PDF page/chunk
└── relationships: list[Relationship]  ← edges between nodes
```

Each `Node` holds a `properties` dict (`page_content`, `summary`, `themes`, `entities`, `embedding`, …).

Each `Relationship` links two nodes with a `type` and score in `properties`.

**Mental model:** Ragas's internal scratchpad — regular data structures (lists + objects), serialized to JSON (`artifacts/cat_health_knowledge_graph.json`). Built for one job: *plan synthetic eval questions*.

---

## 3. What Ragas builds and why

### Stage 1 — Bag of chunks (before transforms)

```text
KnowledgeGraph(nodes: 20, relationships: 0)
```

One node per page. No edges. Can't plan multi-hop questions yet.

### Stage 2 — Enriched graph (after transforms)

Ragas adds to each node:

- **summary** — LLM-generated page summary
- **themes** — broader topics
- **entities** — named entities (cats, conditions, treatments, …)
- **embedding** — vector for similarity

Then it adds **edges** via two relationship builders:

- **`cosine_similarity`** — pages with similar *meaning* (embedding threshold ~0.9)
- **`overlap_score`** — pages sharing *named entities* (fuzzy string match)

```text
KnowledgeGraph(nodes: 20, relationships: N)   # N > 0
```

Node count stays the same. Relationships and properties are what change.

### Stage 3 — Query synthesizers walk the graph

| Query type | Graph usage |
|---|---|
| **Single-hop specific** | One node — answer lives in one chunk |
| **Multi-hop specific** | Path through related nodes — combine concrete details |
| **Multi-hop abstract** | Connected themes across nodes — broader reasoning |

**Graph → outcome link:** Without edges, every question is single-hop. With edges, Ragas can say *"page 7 and page 12 both touch senior cat hydration — combine them into one question."*

---

## 4. Minimal graph theory that actually helps

You don't need a graph theory degree. You need this vocabulary:

| Term | Plain English | Ragas example |
|---|---|---|
| **Node / vertex** | A thing | One PDF page chunk |
| **Edge / link** | A relationship | `cosine_similarity` between two pages |
| **Directed edge** | A → B (one-way) | LangGraph control flow |
| **Undirected edge** | A ↔ B (mutual) | Ragas similarity links (`bidirectional=True`) |
| **Weighted edge** | Link has a score | `cosine_similarity: 0.94` |
| **Neighbor** | Directly connected nodes | Pages related to page 7 |
| **Path** | A → B → C | Multi-hop question spans multiple pages |
| **Subgraph** | Piece of the whole | The 2–3 pages picked for one synthetic question |
| **Traversal** | Walking the graph | Synthesizer selecting a scenario |
| **Edge list** | `relationships[]` as a list | Literally what `knowledge_graph.relationships` is |

**One sentence:** A graph stores *what connects to what* so you can query relationships, not just individual items.

---

## 5. Why graphs are a "common language"

Many AI problems reduce to **things + relationships**:

- Documents relate to documents → Ragas
- Steps follow steps → LangGraph / pipelines
- Tokens attend to tokens → attention (fully connected weighted graph)
- Concepts relate to concepts → knowledge graphs
- Functions depend on functions → dependency graphs

Once you model something as a graph, you can ask universal questions:

- *What's reachable from here?*
- *What's the shortest path?*
- *Which cluster does this belong to?*
- *What breaks if I remove this node?*

Different tools, same underlying question shape. That's why "graph" keeps appearing — it's a reusable way to think about connected structure.

---

## 6. Ragas graph ≠ RAG retrieval graph

Important distinction from this notebook:

| | Ragas graph | RAG app (Breakout Room #2) |
|---|---|---|
| **Purpose** | Generate eval questions | Answer user questions |
| **Storage** | In-memory + JSON artifact | Qdrant vector store |
| **Edges** | Explicit similarity / entity overlap | Implicit via embedding nearest-neighbors |
| **When used** | Once, offline, for dataset creation | Every query, at runtime |

The notebook states this explicitly: *"The knowledge graph is a generation aid. It is not the graph used by the RAG application."*

---

## 7. What to learn vs. what can wait

**Worth knowing now (1–2 hours):**

- Nodes, edges, directed vs undirected, weighted edges
- Paths, neighbors, connectivity
- Traversal conceptually (BFS/DFS — "explore neighbors layer by layer" vs "go deep first")
- Edge list vs adjacency matrix (why a list of relationships is fine)

**Can wait:**

- Planarity, graph coloring, min-cut proofs
- Heavy algorithm complexity theory
- Graph database internals

**Best way to learn it:** In context — inspect `knowledge_graph.relationships`, map edges back to page numbers, then look at Task 5 `synthesizer_name` and ask whether each question needed one node or a path.

---

## 8. Practical inspection checklist (Task 3)

After transforms finish:

1. `print(knowledge_graph)` — nodes stable, relationships > 0
2. Inspection cell — property names on nodes (`summary`, `themes`, `entities`, …)
3. Count relationships by `type` (`cosine_similarity` vs `overlap_score`)
4. Pick one edge → source page, target page, score
5. Optional: browse `artifacts/cat_health_knowledge_graph.json`

---

## 9. Key takeaways

1. **Ragas graph = document relationship map for test generation**, not a general-purpose or agent workflow graph.
2. **It's real but mundane** — lists and objects, not magic — which makes it more understandable, not less.
3. **Edges are the unlock** — they turn a bag of pages into combinable scenarios for multi-hop eval questions.
4. **Graph theory vocabulary transfers** — once you see nodes/edges/paths/neighbors, LangGraph, dependency graphs, and attention all feel like variations on one theme.
5. **The overloaded word is annoying but honest** — these systems really are storing connected structure; the confusion is that *what the nodes and edges mean* differs every time.

---

*Captured from Session 5 walkthrough — synthetic data generation with Ragas + LangSmith.*
