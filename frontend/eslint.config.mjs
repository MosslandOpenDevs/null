import coreWebVitals from "eslint-config-next/core-web-vitals";

export default [
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
  ...coreWebVitals,
  {
    rules: {
      "@next/next/no-img-element": "off",
      // New React Compiler-driven rules in eslint-config-next 16 flag
      // pre-existing patterns; downgraded to warnings until the affected
      // components are refactored (tracked for the UX consolidation pass).
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/purity": "warn",
      "react-hooks/preserve-manual-memoization": "warn",
      "react-hooks/immutability": "warn",
      "react-hooks/refs": "warn",
    },
  },
];
