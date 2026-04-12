import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { vi } from "vitest";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "../../..");
const sourceJsDir = path.join(repoRoot, "assets_src", "js");
const bundleJsDir = path.join(
  repoRoot,
  "wagtail_unveil",
  "static",
  "wagtail_unveil",
  "js",
);

const sourceScriptOrder = [
  "report_core.js",
  "report_filters.js",
  "report_sorting.js",
  "report_row_actions.js",
  "report_batch_runner.js",
  "report_components.js",
];

function setFixtureBody(options = {}) {
  const rowsHtml = options.rowsHtml || "";
  const isPlatformReport = options.reportKind === "platform";

  document.body.innerHTML = isPlatformReport
    ? `
        <button type="button" id="report-retry-button">Retry</button>
        <p>Total: <span id="report-total"></span></p>
        <p>Installed: <span id="report-testable"></span></p>
        <p>Missing: <span id="report-untestable"></span></p>
        <p>Warnings: <span id="report-warning-count"></span></p>
        <p id="report-loading-message"></p>
        <p id="report-error-message"></p>
        <button type="button" id="platform-pypi-lookup-button">Fetch Latest PyPI Versions</button>
        <button type="button" id="platform-markdown-report-button">Render Markdown Report</button>
        <table><tbody id="platform-runtime-body"></tbody></table>
        <table><tbody id="platform-source-body"></tbody></table>
        <table><tbody id="platform-warnings-body"></tbody></table>
        <table><tbody id="platform-packages-body"></tbody></table>
        <div id="platform-markdown-panel" class="hidden">
            <button type="button" id="platform-markdown-copy-button">Copy Markdown</button>
            <textarea id="platform-markdown-output"></textarea>
        </div>
        <table><tbody id="platform-metadata-body"></tbody></table>
    `
    : `
        <div class="filters">
            <unveil-search-input placeholder="Search URLs"></unveil-search-input>
            <unveil-toggle-untestable-button></unveil-toggle-untestable-button>
            <unveil-test-all-button></unveil-test-all-button>
            <unveil-pause-button></unveil-pause-button>
            <unveil-cancel-button></unveil-cancel-button>
            <unveil-reset-button></unveil-reset-button>
        </div>
        <button type="button" id="report-retry-button">Retry</button>
        <p class="test-all-summary hidden" id="test-all-summary"></p>
        <p>Total: <span id="report-total"></span></p>
        <p>Testable: <span id="report-testable"></span></p>
        <p>Untestable: <span id="report-untestable"></span></p>
        <p id="report-loading-message"></p>
        <p id="report-error-message"></p>
        <table>
            <thead>
                <tr>
                    <th data-sort-col="0">Route</th>
                    <th data-sort-col="1">Name</th>
                </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
        </table>
    `;

  document.body.dataset.apiUrl = options.apiUrl || "/unveil/api/backend-urls/";
  document.body.dataset.apiAuthToken = options.apiAuthToken || "";
  document.body.dataset.reportKind = options.reportKind || "backend";
  document.body.dataset.reportAccessToken = options.reportAccessToken || "";
  document.body.dataset.reportState = "loading";
  document.body.dataset.loadingFeedback = "hidden";
}

function evaluateFile(fileName) {
  const filePath = path.join(sourceJsDir, fileName);
  const source = fs.readFileSync(filePath, "utf8");

  window.eval(`${source}\n//# sourceURL=${fileName}`);
}

export function resetReportDom(options = {}) {
  delete window.UnveilReport;

  if (document && document.body && document.body.dataset) {
    delete document.body.dataset.unveilReportInitialized;
  }

  setFixtureBody(options);
}

export function loadSourceScripts(options = {}) {
  const scripts = [...sourceScriptOrder];

  if (options.includeData) {
    scripts.push("report_data.js");
  }

  if (options.includeBootstrap) {
    scripts.push("report_bootstrap.js");
  }

  scripts.forEach((fileName) => {
    evaluateFile(fileName);
  });

  return window.UnveilReport;
}

export function loadBundleScript(options = {}) {
  const bundleName = options.minified
    ? "report.bundle.min.js"
    : "report.bundle.js";
  const bundlePath = path.join(bundleJsDir, bundleName);
  const bundleSource = fs.readFileSync(bundlePath, "utf8");
  window.eval(`${bundleSource}\n//# sourceURL=${bundleName}`);
  return window.UnveilReport;
}

export function stubFetchResponse(payload, options = {}) {
  const status = options.status || 200;
  const ok =
    options.ok !== undefined ? options.ok : status >= 200 && status < 300;
  const mock = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  });

  if (typeof globalThis !== "undefined") {
    globalThis.fetch = mock;
  }

  if (typeof window !== "undefined") {
    window.fetch = mock;
  }

  if (typeof global !== "undefined") {
    global.fetch = mock;
  }

  return mock;
}

export function stubLocationReload() {
  return vi.spyOn(window.location, "reload").mockImplementation(() => {});
}
