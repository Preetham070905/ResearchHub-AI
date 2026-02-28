/**
 * KnowledgeGraphViz — D3.js force-directed graph
 * Zoomable, draggable, clickable nodes.
 * When clicking a node → calls onNodeClick with node data.
 */
import { useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import type { GraphNode, GraphEdge } from '../types/api';

interface Props {
    nodes: GraphNode[];
    edges: GraphEdge[];
    onNodeClick?: (node: GraphNode) => void;
    width?: number;
    height?: number;
}

const NODE_COLORS: Record<string, string> = {
    concept: '#f97316',
    method: '#3b82f6',
    keyword: '#8b5cf6',
    author: '#22c55e',
    dataset: '#ec4899',
    metric: '#06b6d4',
};

export default function KnowledgeGraphViz({
    nodes, edges, onNodeClick, width = 800, height = 500,
}: Props) {
    const svgRef = useRef<SVGSVGElement>(null);

    const drawGraph = useCallback(() => {
        if (!svgRef.current || nodes.length === 0) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove();

        const g = svg.append('g');

        // Zoom
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.3, 5])
            .on('zoom', (event) => g.attr('transform', event.transform));
        svg.call(zoom);

        // Simulation
        const sim = d3.forceSimulation(nodes as d3.SimulationNodeDatum[])
            .force('link', d3.forceLink(edges as d3.SimulationLinkDatum<d3.SimulationNodeDatum>[])
                .id((d: unknown) => (d as GraphNode).id)
                .distance(100))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide(30));

        // Edges
        const link = g.selectAll('.link')
            .data(edges)
            .enter()
            .append('line')
            .attr('class', 'kg-link')
            .attr('stroke', '#d1d5db')
            .attr('stroke-width', 1.5)
            .attr('stroke-opacity', 0.6);

        // Edge labels
        const linkLabel = g.selectAll('.link-label')
            .data(edges)
            .enter()
            .append('text')
            .attr('class', 'kg-link-label')
            .attr('font-size', 9)
            .attr('fill', '#9ca3af')
            .attr('text-anchor', 'middle')
            .text((d: GraphEdge) => d.relation.replace(/_/g, ' '));

        // Nodes
        const node = g.selectAll('.node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'kg-node')
            .attr('cursor', 'pointer')
            .call(d3.drag<SVGGElement, GraphNode>()
                .on('start', (event, d) => {
                    if (!event.active) sim.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                })
                .on('drag', (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on('end', (event, d) => {
                    if (!event.active) sim.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                })
            );

        node.append('circle')
            .attr('r', 14)
            .attr('fill', (d: GraphNode) => NODE_COLORS[d.type] || '#f97316')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);

        node.append('text')
            .attr('dy', 28)
            .attr('text-anchor', 'middle')
            .attr('font-size', 10)
            .attr('font-weight', 600)
            .attr('fill', 'var(--text-body)')
            .text((d: GraphNode) => d.label.length > 20 ? d.label.slice(0, 18) + '…' : d.label);

        node.on('click', (_event: MouseEvent, d: GraphNode) => {
            if (onNodeClick) onNodeClick(d);
        });

        // Tick
        sim.on('tick', () => {
            link
                .attr('x1', (d: unknown) => ((d as { source: GraphNode }).source.x ?? 0))
                .attr('y1', (d: unknown) => ((d as { source: GraphNode }).source.y ?? 0))
                .attr('x2', (d: unknown) => ((d as { target: GraphNode }).target.x ?? 0))
                .attr('y2', (d: unknown) => ((d as { target: GraphNode }).target.y ?? 0));
            linkLabel
                .attr('x', (d: unknown) => {
                    const e = d as { source: GraphNode; target: GraphNode };
                    return ((e.source.x ?? 0) + (e.target.x ?? 0)) / 2;
                })
                .attr('y', (d: unknown) => {
                    const e = d as { source: GraphNode; target: GraphNode };
                    return ((e.source.y ?? 0) + (e.target.y ?? 0)) / 2;
                });
            node.attr('transform', (d: GraphNode) => `translate(${d.x ?? 0},${d.y ?? 0})`);
        });

        return () => { sim.stop(); };
    }, [nodes, edges, width, height, onNodeClick]);

    useEffect(() => {
        const cleanup = drawGraph();
        return () => { if (cleanup) cleanup(); };
    }, [drawGraph]);

    return (
        <div style={{ border: '1px solid #e5e7eb', borderRadius: 12, overflow: 'hidden', background: '#fafafa' }}>
            <svg ref={svgRef} width={width} height={height} />
            {/* Legend */}
            <div style={{ display: 'flex', gap: 12, padding: '8px 14px', borderTop: '1px solid #e5e7eb', flexWrap: 'wrap' }}>
                {Object.entries(NODE_COLORS).map(([type, color]) => (
                    <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, textTransform: 'capitalize' }}>
                        <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
                        {type}
                    </div>
                ))}
            </div>
        </div>
    );
}
