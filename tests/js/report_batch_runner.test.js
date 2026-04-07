import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { loadSourceScripts, resetReportDom } from "./helpers/reportHarness.js";

describe("report batch runner", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    resetReportDom({
      rowsHtml: `
                <tr>
                    <td>one</td>
                    <td>
                        <button type="button" class="test-btn" data-url="/one" data-status-class="status-2xx">Test</button>
                    </td>
                    <td class="status-cell">-</td>
                </tr>
                <tr>
                    <td>two</td>
                    <td>
                        <button type="button" class="test-btn" data-url="/two" data-status-class="status-5xx">Test</button>
                    </td>
                    <td class="status-cell">-</td>
                </tr>
            `,
    });
    loadSourceScripts();
    window.UnveilReport.components.defineCustomElements();

    window.UnveilReport.rowActions.testUrlButton = vi.fn((button, options) => {
      if (options && typeof options.onComplete === "function") {
        setTimeout(() => {
          options.onComplete({
            statusClass: button.dataset.statusClass,
          });
        }, 0);
      }

      return Promise.resolve({
        statusClass: button.dataset.statusClass,
      });
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  test("transitions through running, paused, continued, and finished", async () => {
    const controls = {
      cancelButton: document.querySelector(".cancel-btn"),
      pauseButton: document.querySelector(".pause-btn"),
      summary: document.getElementById("test-all-summary"),
      testAllButton: document.querySelector(".test-all-btn"),
    };

    window.UnveilReport.batchRunner.testAll();

    expect(window.UnveilReport.state.testState.status).toBe("running");

    expect(controls.testAllButton.classList.contains("hidden")).toBe(true);
    expect(controls.pauseButton.classList.contains("hidden")).toBe(false);
    expect(controls.summary.classList.contains("hidden")).toBe(false);

    window.UnveilReport.batchRunner.handlePauseClick();
    expect(window.UnveilReport.state.testState.status).toBe("paused");
    expect(controls.pauseButton.textContent).toBe("Continue");
    expect(controls.cancelButton.classList.contains("hidden")).toBe(false);

    window.UnveilReport.batchRunner.handlePauseClick();
    expect(window.UnveilReport.state.testState.status).toBe("running");
    expect(controls.pauseButton.textContent).toBe("Pause");
    expect(controls.cancelButton.classList.contains("hidden")).toBe(true);

    vi.runAllTimers();
    await Promise.resolve();

    expect(window.UnveilReport.state.testState).toBeNull();
    expect(controls.testAllButton.classList.contains("hidden")).toBe(false);
    expect(controls.pauseButton.classList.contains("hidden")).toBe(true);
    expect(controls.summary.innerHTML).toContain("Results:");
    expect(controls.summary.innerHTML).toContain("out of 2/2");
  });

  test("keeps paused UI state when the in-flight request completes", async () => {
    const controls = {
      cancelButton: document.querySelector(".cancel-btn"),
      pauseButton: document.querySelector(".pause-btn"),
      summary: document.getElementById("test-all-summary"),
    };
    const completions = [];

    window.UnveilReport.rowActions.testUrlButton = vi.fn((button, options) => {
      completions.push(() => {
        options.onComplete({
          statusClass: button.dataset.statusClass,
        });
      });

      return Promise.resolve({
        statusClass: button.dataset.statusClass,
      });
    });

    window.UnveilReport.batchRunner.testAll();
    window.UnveilReport.batchRunner.handlePauseClick();

    expect(window.UnveilReport.state.testState.status).toBe("paused");
    expect(controls.pauseButton.textContent).toBe("Continue");
    expect(controls.cancelButton.classList.contains("hidden")).toBe(false);
    expect(controls.summary.textContent).toBe("Paused: 0/2");

    completions[0]();
    await Promise.resolve();

    expect(window.UnveilReport.state.testState.status).toBe("paused");
    expect(controls.pauseButton.textContent).toBe("Continue");
    expect(controls.cancelButton.classList.contains("hidden")).toBe(false);
    expect(controls.summary.textContent).toBe("Paused: 1/2");

    vi.runOnlyPendingTimers();

    expect(window.UnveilReport.state.testState.nextIndex).toBe(1);
    expect(window.UnveilReport.rowActions.testUrlButton).toHaveBeenCalledTimes(
      1,
    );

    window.UnveilReport.batchRunner.handlePauseClick();

    expect(window.UnveilReport.state.testState.status).toBe("running");
    expect(controls.pauseButton.textContent).toBe("Pause");
    expect(controls.cancelButton.classList.contains("hidden")).toBe(true);
    expect(window.UnveilReport.rowActions.testUrlButton).toHaveBeenCalledTimes(
      2,
    );
  });

  test("finishes when the final in-flight request completes during pause", async () => {
    resetReportDom({
      rowsHtml: `
                <tr>
                    <td>one</td>
                    <td>
                        <button type="button" class="test-btn" data-url="/one" data-status-class="status-2xx">Test</button>
                    </td>
                    <td class="status-cell">-</td>
                </tr>
            `,
    });
    loadSourceScripts();
    window.UnveilReport.components.defineCustomElements();

    const controls = {
      pauseButton: document.querySelector(".pause-btn"),
      summary: document.getElementById("test-all-summary"),
      testAllButton: document.querySelector(".test-all-btn"),
    };
    const completions = [];

    window.UnveilReport.rowActions.testUrlButton = vi.fn((button, options) => {
      completions.push(() => {
        options.onComplete({
          statusClass: button.dataset.statusClass,
        });
      });

      return Promise.resolve({
        statusClass: button.dataset.statusClass,
      });
    });

    window.UnveilReport.batchRunner.testAll();
    window.UnveilReport.batchRunner.handlePauseClick();

    completions[0]();
    await Promise.resolve();

    expect(window.UnveilReport.state.testState).toBeNull();
    expect(controls.testAllButton.classList.contains("hidden")).toBe(false);
    expect(controls.pauseButton.classList.contains("hidden")).toBe(true);
    expect(controls.summary.innerHTML).toContain("Results:");
    expect(controls.summary.innerHTML).toContain("out of 1/1");
  });

  test("cancel clears active state so completions do not queue more work", async () => {
    const completions = [];
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    window.UnveilReport.rowActions.testUrlButton = vi.fn((button, options) => {
      completions.push(() => {
        options.onComplete({
          statusClass: button.dataset.statusClass,
        });
      });

      return Promise.resolve({
        statusClass: button.dataset.statusClass,
      });
    });

    window.UnveilReport.batchRunner.testAll();

    try {
      window.UnveilReport.batchRunner.cancelTests();
    } catch {
      // jsdom may throw for reload; the runner state transition is what matters here.
    }

    expect(window.UnveilReport.state.testState).toBeNull();
    expect(consoleErrorSpy).toHaveBeenCalled();

    completions[0]();
    await Promise.resolve();
    vi.runOnlyPendingTimers();

    expect(window.UnveilReport.rowActions.testUrlButton).toHaveBeenCalledTimes(
      1,
    );
  });
});
