/**
 * AllSections — Renders the full 16-section analysis report.
 * Used by ResearchHubPage and AnalysisPage to display results.
 */
import ReactMarkdown from 'react-markdown';
import type { AnalysisResult } from '../types/api';
import ConfidenceGauge from './ConfidenceGauge';

interface Props {
    result: AnalysisResult;
}

function Section({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
    return (
        <div className="card" style={{ padding: 16, marginBottom: 10 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 18 }}>{icon}</span> {title}
            </h3>
            {children}
        </div>
    );
}

function JsonBlock({ data }: { data: unknown }) {
    if (!data) return <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No data available.</p>;

    if (typeof data === 'string') {
        return (
            <div style={{ fontSize: 12, lineHeight: 1.7 }}>
                <ReactMarkdown>{data}</ReactMarkdown>
            </div>
        );
    }

    if (Array.isArray(data)) {
        return (
            <ul style={{ fontSize: 12, lineHeight: 1.8, margin: 0, paddingLeft: 16 }}>
                {data.map((item, i) => (
                    <li key={i}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
                ))}
            </ul>
        );
    }

    if (typeof data === 'object' && data !== null) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {Object.entries(data as Record<string, unknown>).map(([key, val]) => (
                    <div key={key} style={{
                        padding: '6px 10px', background: 'var(--bg-input)', borderRadius: 6, fontSize: 12,
                    }}>
                        <strong style={{ textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}:</strong>{' '}
                        {typeof val === 'string' ? val : JSON.stringify(val)}
                    </div>
                ))}
            </div>
        );
    }

    return <span style={{ fontSize: 12 }}>{String(data)}</span>;
}

export default function AllSections({ result }: Props) {
    return (
        <div>
            {result.direct_answer && (
                <Section title="Direct Answer" icon="📌">
                    <div style={{ fontSize: 12 }}>
                        <strong>Query:</strong> {result.direct_answer.query}<br />
                        <strong>Papers Found:</strong> {result.direct_answer.papers_found}<br />
                        <strong>Sources:</strong> arXiv ({result.direct_answer.sources?.arxiv ?? 0}), PubMed ({result.direct_answer.sources?.pubmed ?? 0})
                    </div>
                </Section>
            )}

            {result.context_summary && (
                <Section title="Context Summary" icon="📄">
                    <div style={{ fontSize: 12 }}>
                        <strong>{result.context_summary.total_papers} papers analyzed</strong>
                        {result.context_summary.papers?.slice(0, 5).map((p, i) => (
                            <div key={i} style={{ padding: '6px 10px', background: 'var(--bg-input)', borderRadius: 6, marginTop: 6 }}>
                                <strong>{p.title}</strong>
                                <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>{p.authors} • {p.source}</div>
                            </div>
                        ))}
                    </div>
                </Section>
            )}

            {result.comparison && (
                <Section title="Comparative Analysis" icon="⚖️">
                    <JsonBlock data={result.comparison} />
                </Section>
            )}

            {result.deep_insights && (
                <Section title="Deep Insights" icon="💡">
                    <JsonBlock data={result.deep_insights} />
                </Section>
            )}

            {result.gap_analysis && (
                <Section title="Gap Analysis" icon="🔍">
                    <JsonBlock data={result.gap_analysis} />
                </Section>
            )}

            {result.knowledge_graph && (
                <Section title="Knowledge Graph" icon="🕸️">
                    <div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
                        <span className="badge badge-blue">{result.knowledge_graph.node_count} nodes</span>
                        <span className="badge">{result.knowledge_graph.edge_count} edges</span>
                    </div>
                    {result.knowledge_graph.key_concepts && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
                            {result.knowledge_graph.key_concepts.map((c, i) => (
                                <span key={i} className="badge badge-blue" style={{ fontSize: 10 }}>
                                    {typeof c === 'string' ? c : (c as Record<string, unknown>).name ?? JSON.stringify(c)}
                                </span>
                            ))}
                        </div>
                    )}
                    <p style={{ fontSize: 12, lineHeight: 1.6 }}>{result.knowledge_graph.graph_insights}</p>
                </Section>
            )}

            {result.novelty_score && (
                <Section title="Novelty Score" icon="🆕">
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                        <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--accent)' }}>
                            {result.novelty_score.overall_score}/100
                        </div>
                        <div style={{ fontSize: 12, lineHeight: 1.6 }}>
                            {result.novelty_score.explanation}
                        </div>
                    </div>
                </Section>
            )}

            {result.trend_forecast && (
                <Section title="Trend Forecast" icon="📈">
                    <JsonBlock data={result.trend_forecast} />
                </Section>
            )}

            {result.recommended_methods_datasets && (
                <Section title="Recommended Methods & Datasets" icon="🧪">
                    <JsonBlock data={result.recommended_methods_datasets} />
                </Section>
            )}

            {result.experiment_suggestions && (
                <Section title="Experiment Suggestions" icon="🔬">
                    <ul style={{ fontSize: 12, lineHeight: 1.8, margin: 0, paddingLeft: 16 }}>
                        {result.experiment_suggestions.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                </Section>
            )}

            {result.researcher_roadmap && (
                <Section title="Researcher Roadmap" icon="🗺️">
                    <JsonBlock data={result.researcher_roadmap} />
                </Section>
            )}

            {result.argument_strength && (
                <Section title="Argument Strength" icon="⚡">
                    {result.argument_strength.map((a, i) => (
                        <div key={i} style={{
                            padding: 10, background: 'var(--bg-input)', borderRadius: 6, marginBottom: 6, fontSize: 12,
                        }}>
                            <strong>Claim:</strong> {a.claim}<br />
                            <strong>Evidence:</strong> {a.evidence_strength} | <strong>Reliability:</strong> {a.reliability}<br />
                            <strong>Missing:</strong> {a.missing_evidence} | <strong>Bias:</strong> {a.bias_indicators}
                        </div>
                    ))}
                </Section>
            )}

            {result.scientific_critique && (
                <Section title="Scientific Critique" icon="🧐">
                    <JsonBlock data={result.scientific_critique} />
                </Section>
            )}

            {result.literature_review && (
                <Section title="Literature Review" icon="📚">
                    <div style={{ fontSize: 12, lineHeight: 1.7 }}>
                        <ReactMarkdown>{result.literature_review}</ReactMarkdown>
                    </div>
                </Section>
            )}

            {result.final_simplified_answer && (
                <Section title="Final Simplified Answer" icon="✨">
                    <div style={{ fontSize: 12, lineHeight: 1.7 }}>
                        <ReactMarkdown>{result.final_simplified_answer}</ReactMarkdown>
                    </div>
                </Section>
            )}

            {/* Confidence Gauge at the bottom */}
            {result.confidence_score && (
                <div className="card" style={{ padding: 20, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 20 }}>
                    <ConfidenceGauge score={result.confidence_score.overall} size={100} />
                    <div>
                        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 4 }}>Confidence Score</h4>
                        {result.confidence_score.factors && (
                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                {Object.entries(result.confidence_score.factors).map(([k, v]) => (
                                    <span key={k} style={{ marginRight: 12 }}>
                                        {k.replace(/_/g, ' ')}: <strong>{(v * 100).toFixed(0)}%</strong>
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {result.explainability_log && (
                <Section title="Explainability Log" icon="📊">
                    <div style={{ fontSize: 12 }}>
                        <strong>Agents Activated:</strong> {result.explainability_log.agents_activated?.join(', ')}<br />
                        <strong>Total:</strong> {result.explainability_log.total_agents}
                        {result.explainability_log.timing_breakdown && (
                            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                {Object.entries(result.explainability_log.timing_breakdown).map(([k, v]) => (
                                    <span key={k} className="badge" style={{ fontSize: 10 }}>
                                        {k}: {v.toFixed(1)}s
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </Section>
            )}
        </div>
    );
}
