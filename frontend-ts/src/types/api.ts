/* ──────────────────────────────────────────────────────────
   TypeScript interfaces matching the FastAPI backend schemas.
   ────────────────────────────────────────────────────────── */

// ── Auth ──────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// ── Workspace ─────────────────────────────────────────────
export interface Workspace {
  id: number;
  name: string;
}

// ── Papers ────────────────────────────────────────────────
export interface PaperItem {
  id: number;
  filename: string;
  workspace_id: number;
}

export interface SearchPaper {
  title: string;
  authors: string;
  abstract: string;
  year: string;
  source: string;
  url: string;
}

// ── Analysis ──────────────────────────────────────────────
export interface AnalysisHistoryItem {
  id: number;
  query: string;
  created_at: string | null;
}

export interface ChatResponse {
  query: string;
  result: AnalysisResult;
  pipeline_time_seconds: number;
}

export interface AnalysisResult {
  direct_answer?: DirectAnswer;
  context_summary?: ContextSummary;
  knowledge_graph?: KnowledgeGraphData;
  comparison?: Record<string, unknown>;
  gap_analysis?: Record<string, unknown>;
  deep_insights?: Record<string, unknown>;
  novelty_score?: NoveltyScore;
  trend_forecast?: Record<string, unknown>;
  recommended_methods_datasets?: Record<string, unknown>;
  experiment_suggestions?: string[];
  researcher_roadmap?: Record<string, unknown>;
  argument_strength?: ArgumentStrengthItem[];
  scientific_critique?: Record<string, unknown>;
  literature_review?: string;
  final_simplified_answer?: string;
  confidence_score?: ConfidenceScore;
  explainability_log?: ExplainabilityLog;
}

// ── Section types ─────────────────────────────────────────
export interface DirectAnswer {
  query: string;
  intent: Record<string, string>;
  papers_found: number;
  sources: { arxiv: number; pubmed: number };
}

export interface ContextSummary {
  papers: PaperContext[];
  total_papers: number;
}

export interface PaperContext {
  title: string;
  authors: string;
  url: string;
  source: string;
  abstract: string;
}

export interface KnowledgeGraphData {
  node_count: number;
  edge_count: number;
  key_concepts: Array<string | { name: string; centrality: number }>;
  hidden_connections: Array<Record<string, unknown>>;
  graph_insights: string;
  node_type_distribution?: Record<string, number>;
  clusters?: Array<{ size: number; members: string[] }>;
}

export interface NoveltyScore {
  overall_score: number;
  uniqueness_score?: number;
  scientific_novelty_score?: number;
  practical_novelty_score?: number;
  redundancy_risk_score?: number;
  opportunity_score?: number;
  explanation?: string;
  opportunity_areas?: string[];
}

export interface ArgumentStrengthItem {
  claim: string;
  evidence_strength: string;
  reliability: string;
  missing_evidence: string;
  bias_indicators: string;
}

export interface ConfidenceScore {
  overall: number;
  factors: Record<string, number>;
}

export interface ExplainabilityLog {
  agents_activated: string[];
  total_agents: number;
  timing_breakdown: Record<string, number>;
  pipeline_metadata: Record<string, unknown>;
}

// ── D3 Knowledge Graph ────────────────────────────────────
export interface GraphNode {
  id: string;
  type: string;
  label: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  relation: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ── Agent Response ────────────────────────────────────────
export interface AgentResponse {
  agent: string;
  result: Record<string, unknown>;
  graph?: GraphData;
  papers?: SearchPaper[];
}

// ── Conversation ─────────────────────────────────────────
export interface ConversationItem {
  id: number;
  user_message: string;
  ai_response: string;
  timestamp: string;
}
