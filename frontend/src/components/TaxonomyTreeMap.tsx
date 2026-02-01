"use client";

import { useEffect } from "react";
import { useTaxonomyStore, TaxonomyNode } from "@/stores/taxonomy";

interface TaxonomyTreeMapProps {
  onSelectNode?: (nodeId: string) => void;
}

export function TaxonomyTreeMap({ onSelectNode }: TaxonomyTreeMapProps) {
  const { rootNodes, fetchTree } = useTaxonomyStore();

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  if (rootNodes.length === 0) return null;

  const maxCount = Math.max(...rootNodes.map((n) => n.member_count), 1);

  return (
    <div className="w-full">
      <h2 className="text-sm uppercase tracking-widest text-gray-600 mb-3">
        Taxonomy
      </h2>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-1.5">
        {rootNodes.map((node) => {
          const intensity = Math.max(0.15, node.member_count / maxCount);
          return (
            <button
              key={node.id}
              onClick={() => onSelectNode?.(node.id)}
              className="relative px-2 py-3 border border-gray-700 hover:border-accent/60 transition-all text-left group overflow-hidden rounded"
              style={{
                backgroundColor: `rgba(99, 102, 241, ${intensity * 0.2})`,
              }}
            >
              <div className="font-mono text-[10px] text-gray-300 group-hover:text-white truncate">
                {node.label}
              </div>
              <div className="font-mono text-[8px] text-gray-500 mt-0.5">
                {node.member_count} items
              </div>
              {node.description && (
                <div className="font-mono text-[7px] text-gray-600 mt-1 truncate">
                  {node.description}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
