"""
Knowledge Graph Service — builds and analyzes a research concept graph.

WHY A KNOWLEDGE GRAPH:
Text-based LLM analysis is sequential — it reads paper by paper.
A graph finds STRUCTURAL patterns that text misses:
- Two papers using the same dataset but different methods = potential comparison
- Method A improves Method B which contradicts Method C = important insight
- A dataset used by 5 papers but never with technique X = research opportunity

HOW IT WORKS:
1. Extracts concepts from summaries + insights via LLM
2. Builds a NetworkX directed graph
3. Computes centrality (most important nodes), connected components, etc.
4. Detects "hidden links" — connections that span multiple hops but aren't obvious
"""

import json
import logging
from typing import Dict, Any, List
import networkx as nx
from services.llm_service import call_llm_async
from agents.system_prompt import KNOWLEDGE_GRAPH_ROLE

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """Builds and analyzes a knowledge graph from research data."""

    def __init__(self):
        self.graph = nx.DiGraph()

    async def build(
        self,
        summaries: Any,
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build knowledge graph from summaries + insights.

        Steps:
        1. Ask LLM to extract nodes and edges from the research data
        2. Build NetworkX graph
        3. Analyze graph structure
        4. Return insights

        Returns dict with node_count, edge_count, key_concepts,
        hidden_connections, and graph_insights.
        """
        # Step 1: Extract graph elements via LLM
        # If upstream summarizer failed, return empty graph
        if isinstance(summaries, dict) and "error" in summaries:
            return {
                "node_count": 0,
                "edge_count": 0,
                "key_concepts": [],
                "hidden_connections": [],
                "graph_insights": "Knowledge graph unavailable — summarizer failed upstream.",
                "error": summaries["error"]
            }

        graph_data = await self._extract_graph_elements(summaries, insights)

        # Step 2: Build the graph
        self._populate_graph(graph_data)

        # Step 3: Analyze
        analysis = self._analyze_graph()

        return analysis

    async def _extract_graph_elements(
        self,
        summaries: Any,
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ask LLM to identify graph nodes and edges from research data."""
        summaries_text = json.dumps(summaries, indent=2) if not isinstance(summaries, str) else summaries
        insights_text = json.dumps(insights, indent=2) if not isinstance(insights, str) else insights

        messages = [
            {
                "role": "system",
                "content": KNOWLEDGE_GRAPH_ROLE
            },
            {
                "role": "user",
                "content": f"""From this research data, extract a knowledge graph.

=== SUMMARIES ===
{summaries_text}

=== INSIGHTS ===
{insights_text}

Return JSON in this exact format:
{{
    "nodes": [
        {{"id": "node_name", "type": "concept|method|dataset|problem|finding", "description": "brief description"}}
    ],
    "edges": [
        {{"source": "node_name_1", "target": "node_name_2", "relationship": "supports|contradicts|improves|enables|uses|evaluates_on"}}
    ]
}}

Extract at least 20 nodes and 30 edges. JSON only, no markdown."""
            }
        ]

        response = await call_llm_async(messages, max_tokens=3000)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse knowledge graph extraction")
            # Fallback: create a minimal graph from insights
            return self._fallback_extraction(insights)

    def _fallback_extraction(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal graph from insights if LLM extraction fails."""
        nodes = []
        edges = []

        # Extract from insights keys
        for method in insights.get("unique_methods", []):
            name = method if isinstance(method, str) else str(method)
            nodes.append({"id": name, "type": "method", "description": name})

        for dataset in insights.get("common_datasets", []):
            name = dataset if isinstance(dataset, str) else str(dataset)
            nodes.append({"id": name, "type": "dataset", "description": name})

        for theme in insights.get("emerging_themes", []):
            name = theme if isinstance(theme, str) else str(theme)
            nodes.append({"id": name, "type": "concept", "description": name})

        # Create edges between methods and datasets
        methods = [n["id"] for n in nodes if n["type"] == "method"]
        datasets = [n["id"] for n in nodes if n["type"] == "dataset"]

        for m in methods:
            for d in datasets[:2]:  # Connect each method to first 2 datasets
                edges.append({"source": m, "target": d, "relationship": "evaluates_on"})

        return {"nodes": nodes, "edges": edges}

    def _populate_graph(self, graph_data: Dict[str, Any]):
        """Add nodes and edges to the NetworkX graph."""
        for node in graph_data.get("nodes", []):
            self.graph.add_node(
                node.get("id", "unknown"),
                type=node.get("type", "concept"),
                description=node.get("description", "")
            )

        for edge in graph_data.get("edges", []):
            self.graph.add_edge(
                edge.get("source", ""),
                edge.get("target", ""),
                relationship=edge.get("relationship", "related")
            )

    def _analyze_graph(self) -> Dict[str, Any]:
        """Analyze graph structure and extract insights."""
        if len(self.graph.nodes) == 0:
            return {
                "node_count": 0,
                "edge_count": 0,
                "key_concepts": [],
                "hidden_connections": [],
                "graph_insights": "No graph data available."
            }

        # Centrality: which nodes are most connected/important
        try:
            centrality = nx.degree_centrality(self.graph)
            top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        except Exception:
            top_nodes = []

        # Find hidden connections (paths of length 2-3 between unconnected pairs)
        hidden_connections = self._find_hidden_connections()

        # Connected components (undirected view)
        try:
            undirected = self.graph.to_undirected()
            components = list(nx.connected_components(undirected))
            component_info = [
                {"size": len(c), "members": list(c)[:5]}
                for c in sorted(components, key=len, reverse=True)[:5]
            ]
        except Exception:
            component_info = []

        # Node type distribution
        type_counts = {}
        for _, data in self.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        return {
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "key_concepts": [
                {"name": name, "centrality": round(score, 3)}
                for name, score in top_nodes
            ],
            "node_type_distribution": type_counts,
            "clusters": component_info,
            "hidden_connections": hidden_connections,
            "graph_insights": self._generate_insights_text(top_nodes, hidden_connections)
        }

    def _find_hidden_connections(self, max_path_length: int = 3) -> List[Dict]:
        """
        Find pairs of nodes that aren't directly connected
        but have short paths between them — these are "hidden links"
        that researchers might miss.
        """
        hidden = []
        nodes = list(self.graph.nodes)[:30]  # Limit for performance

        for i, source in enumerate(nodes):
            for target in nodes[i + 1:]:
                if not self.graph.has_edge(source, target):
                    try:
                        path = nx.shortest_path(self.graph, source, target)
                        if 2 < len(path) <= max_path_length + 1:
                            hidden.append({
                                "from": source,
                                "to": target,
                                "via": path[1:-1],
                                "path_length": len(path) - 1
                            })
                    except nx.NetworkXNoPath:
                        continue

                if len(hidden) >= 10:
                    break
            if len(hidden) >= 10:
                break

        return hidden

    def _generate_insights_text(self, top_nodes, hidden_connections) -> str:
        """Generate a human-readable summary of graph insights."""
        parts = []

        if top_nodes:
            names = [n[0] for n in top_nodes[:5]]
            parts.append(f"Most central concepts: {', '.join(names)}.")

        if hidden_connections:
            parts.append(
                f"Found {len(hidden_connections)} hidden connections between "
                f"concepts that aren't directly linked but share intermediate relationships."
            )

        if not parts:
            parts.append("Graph constructed but no significant patterns detected.")

        return " ".join(parts)
