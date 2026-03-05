import path from "node:path";
import { fileURLToPath } from "node:url";

import * as esbuild from "esbuild";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const jsEntryPoint = path.join(repoRoot, "scripts", "report.entry.js");
const cssEntryPoint = path.join(repoRoot, "assets_src", "css", "report.css");
const jsOutputDir = path.join(
  repoRoot,
  "wagtail_unveil",
  "static",
  "wagtail_unveil",
  "js",
);
const cssOutputDir = path.join(
  repoRoot,
  "wagtail_unveil",
  "static",
  "wagtail_unveil",
  "css",
);
const watchMode = process.argv.includes("--watch");

const jsBaseConfig = {
  bundle: true,
  entryPoints: [jsEntryPoint],
  format: "iife",
  legalComments: "none",
  logLevel: "info",
  platform: "browser",
  target: ["es2018"],
};

const cssBaseConfig = {
  bundle: true,
  entryPoints: [cssEntryPoint],
  legalComments: "none",
  logLevel: "info",
};

const builds = [
  {
    ...jsBaseConfig,
    minify: false,
    outfile: path.join(jsOutputDir, "report.bundle.js"),
  },
  {
    ...jsBaseConfig,
    minify: true,
    outfile: path.join(jsOutputDir, "report.bundle.min.js"),
  },
  {
    ...cssBaseConfig,
    minify: false,
    outfile: path.join(cssOutputDir, "admin_urls_report.css"),
  },
  {
    ...cssBaseConfig,
    minify: true,
    outfile: path.join(cssOutputDir, "admin_urls_report.min.css"),
  },
];

if (watchMode) {
  const contexts = await Promise.all(
    builds.map((config) => esbuild.context(config)),
  );
  await Promise.all(contexts.map((context) => context.watch()));
  console.log("Watching JS and CSS bundles for changes...");
} else {
  await Promise.all(builds.map((config) => esbuild.build(config)));
}
