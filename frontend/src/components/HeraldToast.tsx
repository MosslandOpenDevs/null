"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useSimulationStore } from "@/stores/simulation";

export function HeraldToast() {
  const { heraldMessages, dismissHerald } = useSimulationStore();

  // Show only the most recent toast
  const latest = heraldMessages[heraldMessages.length - 1];
  if (!latest) return null;

  return (
    <div className="fixed top-4 left-4 z-50 max-w-sm">
      <AnimatePresence mode="wait">
        <motion.div
          key={latest.id}
          initial={{ opacity: 0, x: -20, scale: 0.95 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: -20, scale: 0.95 }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          className="backdrop-blur-xl bg-void/80 border border-herald/30 px-4 py-3 rounded-sm"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-herald">
              ◆ HERALD
            </span>
          </div>
          <p className="font-serif text-sm text-hud-text leading-relaxed herald-glow">
            {latest.text}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={() => dismissHerald(latest.id)}
              className="font-mono text-[10px] text-hud-muted hover:text-hud-text uppercase tracking-wider transition-colors"
            >
              DISMISS
            </button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
