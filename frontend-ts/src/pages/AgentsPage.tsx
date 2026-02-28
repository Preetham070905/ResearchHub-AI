import { Cpu } from 'lucide-react';
import AgentChatPanel from '../components/AgentChatPanel';
import api from '../api/client';

const AGENTS = [
    {
        name: 'Intent Router', icon: '🎯',
        desc: 'Classifies user query into research intent category',
        run: async (q: string) => { const r = await api.agentRouteIntent(q); return r.result; },
    },
    {
        name: 'Paper Search', icon: '📄',
        desc: 'Searches arXiv + PubMed for relevant papers',
        run: async (q: string) => { const r = await api.searchPapers(q); return { papers: r.papers } as Record<string, unknown>; },
    },
    {
        name: 'Summarizer', icon: '📝',
        desc: 'Generates structured summaries of retrieved papers',
        run: async (q: string) => { const r = await api.agentSummarize(q); return r.result; },
    },
    {
        name: 'Comparison Agent', icon: '⚖️',
        desc: 'Compares methodologies, results, and approaches across papers',
        run: async (q: string) => { const r = await api.agentCompare(q); return r.result; },
    },
    {
        name: 'Insight Agent', icon: '💡',
        desc: 'Extracts deep cross-paper insights and hidden patterns',
        run: async (q: string) => { const r = await api.agentInsights(q); return r.result; },
    },
    {
        name: 'Gap Detection', icon: '🔍',
        desc: 'Identifies research gaps and unexplored combinations',
        run: async (q: string) => { const r = await api.agentGaps(q); return r.result; },
    },
    {
        name: 'Novelty Scorer', icon: '🆕',
        desc: 'Scores the novelty and uniqueness of the research area',
        run: async (q: string) => { const r = await api.agentNovelty(q); return r.result; },
    },
    {
        name: 'Trend Forecaster', icon: '📈',
        desc: 'Predicts 1-year and 5-year trends in the research field',
        run: async (q: string) => { const r = await api.agentTrends(q); return r.result; },
    },
    {
        name: 'Critique Agent', icon: '🧐',
        desc: 'Evaluates argument strength, biases, and methodology quality',
        run: async (q: string) => { const r = await api.agentCritique(q); return r.result; },
    },
    {
        name: 'Roadmap Agent', icon: '🗺️',
        desc: 'Creates a 30-day action plan for researchers',
        run: async (q: string) => { const r = await api.agentRoadmap(q); return r.result; },
    },
    {
        name: 'Literature Review', icon: '📚',
        desc: 'Synthesizes a complete literature review narrative',
        run: async (q: string) => { const r = await api.agentLiteratureReview(q); return r.result; },
    },
    {
        name: 'Knowledge Graph', icon: '🕸️',
        desc: 'Builds concept-relationship graph from research data',
        run: async (q: string) => { const r = await api.agentKnowledgeGraph(q); return r.result; },
    },
];

export default function AgentsPage() {
    return (
        <div className="page-content">
            <h2 style={{ marginBottom: 6, fontSize: 20, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Cpu size={20} style={{ color: 'var(--accent)' }} />
                Active Agents
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 }}>
                Interact with each agent individually. Click to expand, enter a query, and see the agent's output.
            </p>

            {/* Data Sources Banner */}
            <div className="card" style={{ padding: '10px 16px', marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, fontWeight: 600 }}>Data Sources:</span>
                <span style={{ fontSize: 12, padding: '2px 8px', borderRadius: 4, background: 'var(--accent-light)' }}>🔬 arXiv</span>
                <span style={{ fontSize: 12, padding: '2px 8px', borderRadius: 4, background: 'var(--accent-light)' }}>🏥 PubMed</span>
                <span style={{ fontSize: 12, padding: '2px 8px', borderRadius: 4, background: 'var(--accent-light)' }}>🧠 Groq LLM (Llama 3.3 70B)</span>
            </div>

            {/* Agent Panels */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {AGENTS.map((agent) => (
                    <AgentChatPanel
                        key={agent.name}
                        name={agent.name}
                        icon={agent.icon}
                        description={agent.desc}
                        onRun={agent.run}
                    />
                ))}
            </div>
        </div>
    );
}
