"use client";

import { useMemo, useRef, useEffect, useState } from "react";
import { useSimulationStore } from "@/stores/simulation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

interface GraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
  type?: string;
}

interface GraphLink {
  source: string;
  target: string;
  predicate: string;
  confidence: number;
  type?: string;
}

interface EntityGraphData {
  nodes: Array<{ id: string; type: string; label: string }>;
  edges: Array<{ source_id: string; target_id: string; type: string; weight: number }>;
}

export function GraphTab() {
  const { knowledgeEdges, world } = useSimulationStore();
  const svgRef = useRef<SVGSVGElement>(null);
  const [entityGraph, setEntityGraph] = useState<EntityGraphData | null>(null);

  useEffect(() => {
    if (!world) return;
    fetch(`${API_URL}/api/worlds/${world.id}/entity-graph`)
      .then((r) => r.json())
      .then(setEntityGraph)
      .catch(() => {});
  }, [world]);

  const { nodes, links } = useMemo(() => {
    const nodeSet = new Set<string>();
    const nodeLabels = new Map<string, { label: string; type: string }>();
    const links: GraphLink[] = [];

    for (const edge of knowledgeEdges) {
      nodeSet.add(edge.subject);
      nodeSet.add(edge.object);
      nodeLabels.set(edge.subject, { label: edge.subject, type: "concept" });
      nodeLabels.set(edge.object, { label: edge.object, type: "concept" });
      links.push({
        source: edge.subject,
        target: edge.object,
        predicate: edge.predicate,
        confidence: edge.confidence,
        type: "knowledge",
      });
    }

    // Add entity graph edges (mention-based)
    if (entityGraph) {
      for (const node of entityGraph.nodes) {
        if (!nodeSet.has(node.id)) {
          nodeSet.add(node.id);
          nodeLabels.set(node.id, { label: node.label, type: node.type });
        }
      }
      for (const edge of entityGraph.edges) {
        links.push({
          source: edge.source_id,
          target: edge.target_id,
          predicate: edge.type,
          confidence: edge.weight,
          type: "mention",
        });
      }
    }

    // Simple circle layout
    const nodeArray = Array.from(nodeSet);
    const nodes: GraphNode[] = nodeArray.map((id, i) => {
      const angle = (2 * Math.PI * i) / Math.max(nodeArray.length, 1);
      const radius = Math.min(130, 40 + nodeArray.length * 8);
      const info = nodeLabels.get(id);
      return {
        id,
        label: info?.label || id,
        x: 175 + Math.cos(angle) * radius,
        y: 175 + Math.sin(angle) * radius,
        type: info?.type || "concept",
      };
    });

    return { nodes, links };
  }, [knowledgeEdges, entityGraph]);

  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  if (knowledgeEdges.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-mono text-[11px] text-hud-muted">
          NO KNOWLEDGE GRAPH DATA
        </span>
      </div>
    );
  }

  return (
    <div className="p-2">
      <svg
        ref={svgRef}
        viewBox="0 0 350 350"
        className="w-full"
        style={{ maxHeight: "calc(100vh - 200px)" }}
      >
        {/* Links */}
        {links.map((link, i) => {
          const s = nodeMap.get(link.source);
          const t = nodeMap.get(link.target);
          if (!s || !t) return null;
          return (
            <g key={i}>
              <line
                x1={s.x}
                y1={s.y}
                x2={t.x}
                y2={t.y}
                stroke={link.type === "mention" ? "#6366f1" : "#2a2a4e"}
                strokeWidth={Math.max(0.5, link.confidence * 2)}
                strokeOpacity={link.type === "mention" ? 0.4 : 0.6}
                strokeDasharray={link.type === "mention" ? "2,2" : undefined}
              />
              <text
                x={(s.x + t.x) / 2}
                y={(s.y + t.y) / 2 - 4}
                fill="#3a3a4e"
                fontSize="6"
                fontFamily="monospace"
                textAnchor="middle"
              >
                {link.predicate}
              </text>
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const color = node.type === "agent" ? "#22c55e" : node.type === "wiki_page" ? "#eab308" : "#6366f1";
          return (
          <g key={node.id} className="cursor-pointer">
            <circle
              cx={node.x}
              cy={node.y}
              r={4}
              fill={color}
              fillOpacity={0.6}
              stroke={color}
              strokeWidth={0.5}
            />
            <text
              x={node.x}
              y={node.y + 10}
              fill="#c8c8d4"
              fontSize="7"
              fontFamily="monospace"
              textAnchor="middle"
            >
              {node.label.length > 15 ? node.label.slice(0, 15) + "…" : node.label}
            </text>
          </g>
          );
        })}
      </svg>

      {/* Edge count */}
      <div className="font-mono text-[9px] text-hud-label text-center mt-2">
        {nodes.length} NODES · {links.length} EDGES
      </div>
    </div>
  );
}
