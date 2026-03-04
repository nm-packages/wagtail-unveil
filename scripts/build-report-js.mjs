import path from "node:path";
import { fileURLToPath } from "node:url";

import * as esbuild from "esbuild";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const entryPoint = path.join(repoRoot, "scripts", "report.entry.js");
const outputDir = path.join(
  repoRoot,
  "wagtail_unveil",
  "static",
  "wagtail_unveil",
  "js",
);
const watchMode = process.argv.includes("--watch");

const baseConfig = {
  bundle: true,
  entryPoints: [entryPoint],
  format: "iife",
  legalComments: "none",
  logLevel: "info",
  platform: "browser",
  target: ["es2018"],
};

const builds = [
  {
    ...baseConfig,
    minify: false,
    outfile: path.join(outputDir, "report.bundle.js"),
  },
  {
    ...baseConfig,
    minify: true,
    outfile: path.join(outputDir, "report.bundle.min.js"),
  },
];

if (watchMode) {
  const contexts = await Promise.all(
    builds.map((config) => esbuild.context(config)),
  );
  await Promise.all(contexts.map((context) => context.watch()));
  console.log("Watching JS bundles for changes...");
} else {
  await Promise.all(builds.map((config) => esbuild.build(config)));
}
