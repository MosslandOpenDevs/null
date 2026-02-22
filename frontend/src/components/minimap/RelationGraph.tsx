"use client";

import { useEffect, useRef, useMemo, useState } from "react";
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3-force";
import { useSimulationStore } from "@/stores/simulation";

interface GraphNode extends SimulationNodeDatum {
  id: string;
  name: string;
  factionColor: string;
  factionId: string | null;
  active: boolean;
}

interface GraphLink extends SimulationLinkDatum<GraphNode> {
  type: string;
  strength: number;
}

interface RelationGraphProps {
  onAgentClick?: (agentId: string) => void;
  activeAgentIds?: Set<string>;
}

export function RelationGraph({ onAgentClick, activeAgentIds }: RelationGraphProps) {
  const { agents, factions, relationships } = useSimulationStore();
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const factionMap = useMemo(
    () => new Map(factions.map((f) => [f.id, f])),
    [factions]
  );

  // Build graph data
  useEffect(() => {
    const graphNodes: GraphNode[] = agents.map((a) => {
      const faction = a.faction_id ? factionMap.get(a.faction_id) : null;
      return {
        id: a.id,
        name: a.name,
        factionColor: faction?.color || "#6366f1",
        factionId: a.faction_id,
        active: activeAgentIds?.has(a.id) ?? false,
      };
    });

    const nodeSet = new Set(graphNodes.map((n) => n.id));
    const graphLinks: GraphLink[] = relationships
      .filter((r) => nodeSet.has(r.agent_a) && nodeSet.has(r.agent_b))
      .map((r) => ({
        source: r.agent_a,
        target: r.agent_b,
        type: r.type,
        strength: r.strength,
      }));

    const sim = forceSimulation<GraphNode>(graphNodes)
      .force(
        "link",
        forceLink<GraphNode, GraphLink>(graphLinks)
          .id((d) => d.id)
          .distance(40)
          .strength((d) => Math.abs(d.strength) * 0.5)
      )
      .force("charge", forceManyBody().strength(-30))
      .force("center", forceCenter(120, 100))
      .force("collide", forceCollide(12));

    sim.on("tick", () => {
      setNodes([...graphNodes]);
      setLinks([...graphLinks]);
    });

    // Run simulation synchronously for quick layout
    sim.alpha(1).restart();

    return () => {
      sim.stop();
    };
  }, [agents, factions, relationships, factionMap, activeAgentIds]);

  const getLinkColor = (link: GraphLink): string => {
    if (link.strength > 0.3) return "#4488ff"; // alliance / positive
    if (link.strength < -0.3) return "#ff4466"; // hostile
    return "#3d3d52"; // neutral
  };

  return (
    <svg
      ref={svgRef}
      viewBox="0 0 240 200"
      className="w-full h-auto"
    >
      {/* Glow filter */}
      <defs>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Links */}
      {links.map((link, i) => {
        const source = link.source as GraphNode;
        const target = link.target as GraphNode;
        if (!source.x || !source.y || !target.x || !target.y) return null;

        return (
          <line
            key={i}
            x1={source.x}
            y1={source.y}
            x2={target.x}
            y2={target.y}
            stroke={getLinkColor(link)}
            strokeWidth={Math.max(0.5, Math.abs(link.strength) * 2)}
            strokeOpacity={Math.max(0.15, Math.abs(link.strength) * 0.6)}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => {
        if (!node.x || !node.y) return null;
        const isHovered = hoveredNode === node.id;
        const isActive = node.active;

        return (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={isHovered ? 7 : isActive ? 6 : 4}
              fill={node.factionColor}
              opacity={isActive ? 1 : 0.6}
              filter={isActive ? "url(#glow)" : undefined}
              className="cursor-pointer transition-all"
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              onClick={() => onAgentClick?.(node.id)}
            />
            {isHovered && (
              <text
                x={node.x}
                y={node.y - 10}
                textAnchor="middle"
                fill="#e0dfd8"
                fontSize="8"
                fontFamily="JetBrains Mono, monospace"
              >
                {node.name}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
