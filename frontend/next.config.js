const path = require("path");
const withNextIntl = require("next-intl/plugin")("./src/i18n/request.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Pin file tracing to the monorepo root so the standalone bundle lands at
  // .next/standalone/frontend/server.js regardless of where the repo is checked out.
  outputFileTracingRoot: path.join(__dirname, ".."),
};

module.exports = withNextIntl(nextConfig);
