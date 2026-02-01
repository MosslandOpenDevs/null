"use client";

import { useMemo, useRef, useEffect, useCallback } from "react";
import { useSimulationStore } from "@/stores/simulation";

interface GraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
}

interface GraphLink {
  source: string;
  target: string;
  predicate: string;
  confidence: number;
}

export function GraphTab() {
  const { knowledgeEdges, setIntelTab } = useSimulationStore();
  const svgRef = useRef<SVGSVGElement>(null);

  const { nodes, links } = useMemo(() => {
    const nodeSet = new Set<string>();
    const links: GraphLink[] = [];

    for (const edge of knowledgeEdges) {
      nodeSet.add(edge.subject);
      nodeSet.add(edge.object);
      links.push({
        source: edge.subject,
        target: edge.object,
        predicate: edge.predicate,
        confidence: edge.confidence,
      });
    }

    // Simple circle layout
    const nodeArray = Array.from(nodeSet);
    const nodes: GraphNode[] = nodeArray.map((id, i) => {
      const angle = (2 * Math.PI * i) / Math.max(nodeArray.length, 1);
      const radius = Math.min(130, 40 + nodeArray.length * 8);
      return {
        id,
        label: id,
        x: 175 + Math.cos(angle) * radius,
        y: 175 + Math.sin(angle) * radius,
      };
    });

    return { nodes, links };
  }, [knowledgeEdges]);

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
                stroke="#2a2a4e"
                strokeWidth={Math.max(0.5, link.confidence * 2)}
                strokeOpacity={0.6}
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
        {nodes.map((node) => (
          <g key={node.id} className="cursor-pointer">
            <circle
              cx={node.x}
              cy={node.y}
              r={4}
              fill="#6366f1"
              fillOpacity={0.6}
              stroke="#6366f1"
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
        ))}
      </svg>

      {/* Edge count */}
      <div className="font-mono text-[9px] text-hud-label text-center mt-2">
        {nodes.length} NODES · {links.length} EDGES
      </div>
    </div>
  );
}
