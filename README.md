<div align="center">

# 🧠 ResearchHub AI

### Agentic Multi-Agent Scientific Reasoning Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.131-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**An end-to-end AI-powered research assistant that orchestrates 11 specialized agents to transform any research question into a comprehensive 16-section scientific analysis — complete with paper retrieval, knowledge graphs, novelty scoring, trend forecasting, and actionable roadmaps.**

[Features](#-key-features) · [Architecture](#-system-architecture) · [Setup](#-getting-started) · [API](#-api-endpoints) · [Uniqueness](#-what-makes-this-unique)

</div>

---

## 📋 Table of Contents

- [Why ResearchHub AI?](#-why-researchhub-ai)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Pipeline Flow](#-pipeline-flow--agent-dependency-graph)
- [The 16-Section Output](#-pipeline-output-sections)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [API Endpoints](#-api-endpoints)
- [What Makes This Unique](#-what-makes-this-unique)
- [Future Scope](#-future-scope)
- [Author](#-author)

---

## ❓ Why ResearchHub AI?

Academic research today is **drowning in information overload**. Every year, over **5 million** new papers are published across arXiv, PubMed, and other repositories. Researchers face critical challenges:

| Problem | Impact |
|---------|--------|
| **Information overload** | A single literature review takes 2–6 weeks of manual reading |
| **Siloed analysis** | Researchers compare papers mentally — missing cross-domain patterns |
| **Missed connections** | Hidden links between methods, datasets, and findings go unnoticed |
| **No structured workflow** | No tool combines search → summarize → compare → identify gaps → plan next steps |
| **Bias blind spots** | Individual researchers carry unconscious biases into their reviews |

**ResearchHub AI solves all of these** by deploying a team of 11 specialized AI agents that work together — like a research lab — to produce a structured, reproducible, and comprehensive analysis in **under 60 seconds**.

---

## ✨ Key Features

- 🔍 **Dual-Source Paper Search** — Concurrent retrieval from arXiv + PubMed via async APIs
- 📄 **PDF Upload & Extraction** — Upload your own papers; text is extracted and merged into the analysis
- 📝 **Structured Summarization** — Each paper broken into: Problem, Methodology, Dataset, Metrics, Results, Limitations
- ⚖️ **Cross-Paper Comparison** — Side-by-side analysis of methodologies, datasets, and trade-offs
- 💡 **Deep Insight Extraction** — Identifies emerging themes, unique methods, and common patterns across papers
- 🔬 **Research Gap Detection** — Automatically surfaces unexplored areas and proposes experiments
- 🕸️ **Knowledge Graph Construction** — Builds a directed graph of concepts, methods, and datasets using NetworkX; computes centrality and hidden connections
- 🆕 **Novelty Scoring** — 5-dimensional scoring (uniqueness, scientific, practical, redundancy risk, opportunity)
- 📈 **Trend Forecasting** — 1-year and 3-year research trajectory predictions
- 🧐 **Scientific Critique** — Evaluates argument strength, evidence reliability, and bias indicators
- 🗺️ **30-Day Researcher Roadmap** — Week-by-week learning plan with projects, datasets, and baselines
- 📚 **Automated Literature Review** — Generates a structured academic review (no fabricated citations)
- ✨ **Final Simplified Answer** — A layperson-friendly 2–3 paragraph synthesis
- 📊 **Confidence Scoring** — Data-driven quality score (0–100) with breakdown
- 🔐 **JWT Authentication** — Secure user accounts with bcrypt password hashing
- 🗂️ **Workspace Management** — Organize research by topic with isolated paper collections and analysis history
- ⚡ **Parallel Agent Execution** — Independent agents run concurrently via `asyncio.gather()` for ~50% faster pipelines
- 🛡️ **Graceful Degradation** — If any agent fails, the rest still complete; partial results are always returned

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + TypeScript)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │Dashboard │ │Analysis  │ │ Papers   │ │ Knowledge Graph   │  │
│  │  Page    │ │  Page    │ │  Page    │ │ Visualization     │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬──────────┘  │
│       └─────────────┴────────────┴────────────────┘             │
│                         │ Axios HTTP                            │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + Python)                   │
│                                                                  │
│  ┌─────────┐  ┌──────────────────────────────────────────────┐  │
│  │  Auth   │  │         Agent Orchestrator                    │  │
│  │ (JWT +  │  │                                               │  │
│  │ bcrypt) │  │  Step 1: Intent Router                       │  │
│  └─────────┘  │  Step 2: Paper Search (arXiv + PubMed)       │  │
│               │  Step 3: Summarizer Agent                     │  │
│  ┌─────────┐  │  Step 4: Comparison ║ Insight    (parallel)  │  │
│  │  SQLite │  │  Step 5: Gap Detection Agent                 │  │
│  │   DB    │  │  Step 6: KG ║ Novelty ║ Trend ║ Critique     │  │
│  │(SQLAlch)│  │                              (parallel)       │  │
│  └─────────┘  │  Step 7: Roadmap ║ Literature  (parallel)    │  │
│               │  Step 8: Final Answer Synthesis               │  │
│               │  Step 9: Confidence Scoring + Assembly        │  │
│               └──────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Services: Groq LLM │ Paper Search │ PDF Extractor │ KG │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│               GRAPH RAG MODULE (Standalone)                      │
│  PDF → LangChain Chunking → Groq LLM → Neo4j Knowledge Graph   │
│  Interactive Cypher-based Q&A over the graph                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Pipeline Flow — Agent Dependency Graph

When a user submits a research query, the orchestrator executes agents in optimized dependency order:

```
                        ┌──────────────┐
                        │  User Query  │
                        └──────┬───────┘
                               ▼
                     ┌──────────────────┐
                     │  Intent Router   │  ← Classifies into 7 types
                     └──────┬───────────┘
                            ▼
              ┌──────────────────────────┐
              │  Paper Search + PDF      │  ← arXiv + PubMed + uploads
              │  Extraction (concurrent) │
              └──────────┬───────────────┘
                         ▼
                ┌──────────────────┐
                │   Summarizer     │  ← Structured per-paper summaries
                └────────┬─────────┘
                         │
                ┌────────┴────────┐
                ▼                 ▼
        ┌──────────────┐  ┌──────────────┐
        │  Comparison  │  │   Insight    │  ← PARALLEL
        └──────┬───────┘  └──────┬───────┘
               └────────┬────────┘
                        ▼
               ┌──────────────────┐
               │  Gap Detection   │  ← Needs summaries + comparison + insights
               └────────┬─────────┘
                        │
          ┌─────────┬───┴───┬──────────┐
          ▼         ▼       ▼          ▼
      ┌──────┐ ┌───────┐┌──────┐ ┌────────┐
      │  KG  │ │Novelty││Trend │ │Critique│  ← PARALLEL
      └──────┘ └───────┘└──────┘ └────────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
      ┌──────────────┐   ┌──────────────┐
      │  Literature  │   │   Roadmap    │    ← PARALLEL
      │   Review     │   └──────────────┘
      └──────┬───────┘
             ▼
    ┌──────────────────┐
    │  Final Synthesis │  ← Layperson-friendly answer
    └──────┬───────────┘
           ▼
  ┌──────────────────────┐
  │  16-Section Assembly │  ← Confidence scoring + timing log
  └──────────────────────┘
```

**Parallelization Strategy:**
- **Step 4:** Comparison + Insight run simultaneously (both only need summaries)
- **Step 6:** KG + Novelty + Trend + Critique run as a parallel batch
- **Step 7:** Roadmap + Literature Review run in parallel
- **Result:** ~12 LLM calls complete in ~4 parallel batches instead of 12 sequential ones

---

## 📊 Pipeline Output Sections

The pipeline produces a **16-section** structured analysis:

| # | Section | Description |
|---|---------|-------------|
| 1 | **Direct Answer** | Query echo, intent classification, paper count, source breakdown |
| 2 | **Context Summary** | Paper metadata (titles, authors, URLs, abstracts) |
| 3 | **Knowledge Graph** | Node/edge counts, key concepts by centrality, hidden connections |
| 4 | **Comparative Analysis** | Cross-paper comparison of methods, datasets, and trade-offs |
| 5 | **Gap Analysis** | Research gaps, unexplored combinations, proposed experiments |
| 6 | **Deep Insights** | Emerging themes, unique methods, common patterns |
| 7 | **Novelty Score** | 5-dimensional score (0–100) with explanation |
| 8 | **Trend Forecast** | 1-year and 3-year research trajectory predictions |
| 9 | **Methods & Datasets** | Recommended methods and datasets for the research area |
| 10 | **Experiment Suggestions** | Concrete experiment proposals based on detected gaps |
| 11 | **Researcher Roadmap** | 30-day week-by-week plan with projects, datasets, baselines |
| 12 | **Argument Strength** | Per-claim evidence evaluation with bias indicators |
| 13 | **Scientific Critique** | Strong points, weak points, methodology assessment |
| 14 | **Literature Review** | Structured academic review (no fabricated citations) |
| 15 | **Confidence Score** | Data-driven quality score (0–100) with factor breakdown |
| 16 | **Explainability Log** | Agents activated, timing per step, reasoning summary |

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | High-performance async web framework |
| **Groq (LLaMA 3.3 70B)** | LLM inference via Groq's ultra-fast API |
| **SQLAlchemy** | ORM for database operations |
| **SQLite** | Lightweight database (swappable to PostgreSQL) |
| **NetworkX** | Knowledge graph construction & analysis |
| **httpx** | Async HTTP client for arXiv/PubMed APIs |
| **PyMuPDF** | PDF text extraction |
| **python-jose + bcrypt** | JWT authentication + password hashing |
| **Pydantic** | Request/response validation & settings management |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **React 19** | UI framework |
| **TypeScript 5.9** | Type-safe development |
| **Vite 7** | Lightning-fast build tool |
| **D3.js** | Knowledge graph visualization |
| **React Router 7** | Client-side routing |
| **Axios** | HTTP client with interceptors |
| **Lucide React** | Icon library |
| **React Markdown** | Rendering LLM markdown outputs |

### Graph RAG Module
| Technology | Purpose |
|-----------|---------|
| **Neo4j** | Graph database for entity-relationship storage |
| **LangChain** | PDF loading, text splitting, graph transformation |
| **Groq LLM** | Entity/relationship extraction from text |
| **Docker** | Neo4j containerization |

---

## 📁 Project Structure

```
ResearchHub-AI/
│
├── backend/                        # FastAPI multi-agent analysis server
│   ├── main.py                     # FastAPI entry point (v4.0) — CORS, routers
│   ├── config.py                   # Centralized Pydantic settings from .env
│   ├── database.py                 # SQLAlchemy engine, session, init_db()
│   ├── models.py                   # DB models: User, Workspace, Paper, AnalysisResult, Conversation
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── auth.py                     # JWT + bcrypt authentication
│   │
│   ├── agents/                     # 🧠 11 AI Agents
│   │   ├── orchestrator.py         # Master controller — chains & parallelizes all agents
│   │   ├── intent_router.py        # Classifies query into 7 research intent types
│   │   ├── summarizer_agent.py     # Structured per-paper summarization
│   │   ├── comparison_agent.py     # Cross-paper comparative analysis
│   │   ├── insight_agent.py        # Theme/pattern extraction across papers
│   │   ├── gap_agent.py            # Research gap detection + experiment proposals
│   │   ├── literature_agent.py     # Automated literature review generation
│   │   ├── novelty_agent.py        # 5-dimensional novelty scoring
│   │   ├── trend_agent.py          # Research trend forecasting
│   │   ├── critique_agent.py       # Scientific critique + argument strength
│   │   ├── roadmap_agent.py        # 30-day researcher learning roadmap
│   │   └── system_prompt.py        # All agent role definitions + shared preamble
│   │
│   ├── services/                   # Core services
│   │   ├── llm_service.py          # Async Groq LLM client with retry + rate limiting
│   │   ├── paper_search.py         # arXiv + PubMed concurrent paper retrieval
│   │   ├── pdf_extractor.py        # PDF text extraction from uploaded files
│   │   └── knowledge_graph.py      # NetworkX graph builder + analysis
│   │
│   ├── routers/                    # API route handlers
│   │   ├── auth_router.py          # /auth/register, /auth/login
│   │   ├── workspace_router.py     # /workspaces/ CRUD
│   │   ├── paper_router.py         # /papers/ upload, list, download, import
│   │   ├── chat_router.py          # /chat/analyze — main pipeline endpoint
│   │   └── agent_router.py         # /agents/ — individual agent endpoints
│   │
│   └── requirements.txt
│
├── frontend-ts/                    # React + TypeScript UI
│   ├── src/
│   │   ├── App.tsx                 # Router + protected routes + layout
│   │   ├── main.tsx                # React entry point
│   │   ├── index.css               # Global styles (dark sidebar, glassmorphism)
│   │   │
│   │   ├── api/
│   │   │   └── client.ts           # Axios API client wrapping all backend endpoints
│   │   │
│   │   ├── context/
│   │   │   └── AuthContext.tsx      # Auth state, workspace management, token persistence
│   │   │
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx        # Login + registration
│   │   │   ├── DashboardPage.tsx    # Workspace management + analysis history
│   │   │   ├── AnalysisPage.tsx     # Full pipeline execution + 16-section results
│   │   │   ├── PapersPage.tsx       # PDF upload + paper management
│   │   │   ├── PaperSearchPage.tsx  # arXiv/PubMed search + import to workspace
│   │   │   ├── GraphPage.tsx        # D3.js knowledge graph visualization
│   │   │   ├── AgentsPage.tsx       # Individual agent testing
│   │   │   ├── InsightsPage.tsx     # Insights dashboard
│   │   │   └── ResearchHubPage.tsx  # Combined research hub interface
│   │   │
│   │   ├── components/
│   │   │   ├── AllSections.tsx      # Renders all 16 analysis sections
│   │   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   │   ├── Navbar.tsx           # Top navigation bar
│   │   │   ├── ConfidenceGauge.tsx  # Circular confidence score gauge
│   │   │   ├── KnowledgeGraphViz.tsx # D3.js force-directed graph
│   │   │   ├── TimingCards.tsx      # Pipeline timing breakdown cards
│   │   │   ├── SystemStatus.tsx     # System health status panel
│   │   │   └── SectionCard.tsx      # Reusable analysis section card
│   │   │
│   │   └── types/
│   │       └── api.ts              # TypeScript interfaces for all API types
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── graph_rag/                      # Standalone Graph RAG Pipeline
│   ├── pipeline.py                 # PDF → chunks → LLM extraction → Neo4j
│   ├── graph_rag.py                # Interactive Cypher-based Q&A
│   ├── docker-compose.yml          # Neo4j Docker setup
│   ├── requirements.txt
│   └── files/                      # PDF files for ingestion
│
├── .gitignore
├── .env.example                    # Environment variable template
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Groq API Key** — Free at [console.groq.com](https://console.groq.com)
- **Docker** (optional, for Graph RAG Neo4j module)

### 1. Clone the Repository

```bash
git clone https://github.com/Preetham070905/ResearchHub-AI.git
cd ResearchHub-AI
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your keys:
#   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
#   GROQ_API_KEY=<your Groq API key>

# Start the server
python -m uvicorn main:app --reload --port 8000
```

**API Docs:** http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend-ts

# Install dependencies
npm install

# Create environment file
echo VITE_API_URL=http://localhost:8000 > .env

# Start development server
npm run dev
```

**App URL:** http://localhost:5173

### 4. Graph RAG Module (Optional)

```bash
cd graph_rag

# Start Neo4j via Docker
docker compose up -d

# Install dependencies
pip install -r requirements.txt

# Place PDFs in the files/ directory, then:
python pipeline.py       # Ingest PDFs into Neo4j
python graph_rag.py      # Interactive Q&A
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user (email + password) |
| POST | `/auth/login` | Login → returns JWT access token |

### Workspaces
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces/` | List user's workspaces |
| POST | `/workspaces/` | Create a new workspace |
| PATCH | `/workspaces/{id}` | Rename workspace |
| DELETE | `/workspaces/{id}` | Delete workspace |

### Papers
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/papers/{workspace_id}` | Upload a PDF paper |
| GET | `/papers/{workspace_id}` | List papers in workspace |
| DELETE | `/papers/{workspace_id}/{paper_id}` | Delete a paper |
| POST | `/papers/{workspace_id}/import` | Import paper from search results |
| GET | `/papers/{workspace_id}/{paper_id}/download` | Download a paper |

### Analysis Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/analyze` | **Run full 11-agent pipeline** → 16-section output |
| GET | `/chat/history/{workspace_id}` | Get past analysis results |
| GET | `/chat/result/{analysis_id}` | Get full result for a specific analysis |
| GET | `/chat/conversations/{workspace_id}` | Get conversation history |

### Individual Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/search-papers` | Search arXiv + PubMed |
| POST | `/agents/summarize` | Run summarizer agent only |
| POST | `/agents/compare` | Run comparison agent only |
| POST | `/agents/insights` | Run insight agent only |
| POST | `/agents/gaps` | Run gap detection agent only |
| POST | `/agents/trends` | Run trend agent only |
| POST | `/agents/novelty` | Run novelty scoring agent only |
| POST | `/agents/critique` | Run critique agent only |
| POST | `/agents/roadmap` | Run roadmap agent only |
| POST | `/agents/literature-review` | Run literature review agent only |
| POST | `/agents/knowledge-graph` | Run knowledge graph builder only |
| POST | `/agents/route-intent` | Run intent classifier only |

---

## 🌟 What Makes This Unique

| Feature | ResearchHub AI | ChatGPT / Perplexity | Semantic Scholar | Elicit |
|---------|---------------|----------------------|-----------------|--------|
| Multi-agent orchestration | ✅ 11 specialized agents | ❌ Single model | ❌ | ❌ |
| Real-time paper retrieval | ✅ arXiv + PubMed live | ❌ Training cutoff | ✅ | ✅ |
| Knowledge graph construction | ✅ NetworkX + centrality | ❌ | ❌ | ❌ |
| 5-dimensional novelty scoring | ✅ | ❌ | ❌ | ❌ |
| Research gap detection | ✅ With experiment proposals | ❌ | ❌ | Partial |
| Trend forecasting | ✅ 1-year + 3-year | ❌ | ❌ | ❌ |
| 30-day researcher roadmap | ✅ | ❌ | ❌ | ❌ |
| Argument strength analysis | ✅ Per-claim with bias detection | ❌ | ❌ | ❌ |
| Confidence scoring | ✅ Data-driven 0–100 | ❌ | ❌ | ❌ |
| Upload your own PDFs | ✅ | ❌ | ❌ | ✅ |
| Workspace-based organization | ✅ | ❌ | ❌ | ✅ |
| Full explainability log | ✅ Per-agent timing + reasoning | ❌ | ❌ | ❌ |
| Graceful degradation | ✅ Partial results on failure | ❌ | N/A | ❌ |

---

## 🔮 Future Scope

- **🔗 Selective Agent Routing** — Run only relevant agents based on intent classification (currently all agents always run)
- **📊 Embedding-based Semantic Search** — Use sentence-transformers for similarity-based paper retrieval beyond keyword search
- **🌐 Additional Paper Sources** — Integration with Semantic Scholar, Google Scholar, IEEE Xplore, and DBLP
- **💬 Multi-turn Conversational Analysis** — Follow-up questions that refine previous results without re-running the full pipeline
- **📈 Real-time Collaboration** — Multiple researchers working on the same workspace with live updates
- **🧪 Experiment Tracker** — Track suggested experiments and their outcomes
- **🔄 Incremental Knowledge Graphs** — Persistent graphs that grow with each analysis, building a personal research knowledge base
- **📱 Mobile-Responsive UI** — Responsive design for tablets and mobile devices
- **🤖 Custom Model Support** — Pluggable LLM backends (OpenAI, Anthropic, local models via Ollama)
- **📦 Export to LaTeX/PDF** — One-click export of literature reviews and analysis reports
- **🔍 Citation Network Analysis** — Track citation chains and identify seminal/influential papers
- **🧬 Domain-Specific Agents** — Specialized agents for biomedical, CS, physics, and social science domains

---

## 🧑‍💻 Author

**Partha Kesav Reddy Chundi**

---

## 📄 License

This project is open source under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built with ❤️ using FastAPI, React, Groq, and a lot of research papers.</sub>
</div>
