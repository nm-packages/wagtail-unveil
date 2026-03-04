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

        expect(controls.testAllButton.classList.contains("hidden")).toBe(true);
        expect(controls.pauseButton.classList.contains("hidden")).toBe(false);
        expect(controls.summary.classList.contains("hidden")).toBe(false);

        window.UnveilReport.batchRunner.handlePauseClick();
        expect(controls.pauseButton.textContent).toBe("Continue");
        expect(controls.cancelButton.classList.contains("hidden")).toBe(false);

        window.UnveilReport.batchRunner.handlePauseClick();
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
});
