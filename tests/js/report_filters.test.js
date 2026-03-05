import { beforeEach, describe, expect, test } from "vitest";

import { loadSourceScripts, resetReportDom } from "./helpers/reportHarness.js";

describe("report filters", () => {
  beforeEach(() => {
    resetReportDom({
      rowsHtml: `
                <tr id="row-alpha"><td>alpha route</td><td>alpha</td></tr>
                <tr id="row-beta"><td>beta route</td><td>beta</td></tr>
            `,
    });
    loadSourceScripts();
    window.UnveilReport.components.defineCustomElements();
  });

  test("typing in search input filters rows", () => {
    const input = document.querySelector(".search-input");
    const clear = document.querySelector(".search-clear");
    const alphaRow = document.getElementById("row-alpha");
    const betaRow = document.getElementById("row-beta");

    input.value = "beta";
    input.dispatchEvent(new Event("input"));

    expect(alphaRow.classList.contains("hidden")).toBe(true);
    expect(betaRow.classList.contains("hidden")).toBe(false);
    expect(clear.classList.contains("hidden")).toBe(false);
  });

  test("clear action resets search state", () => {
    const input = document.querySelector(".search-input");
    const clear = document.querySelector(".search-clear");
    const alphaRow = document.getElementById("row-alpha");
    const betaRow = document.getElementById("row-beta");

    input.value = "beta";
    input.dispatchEvent(new Event("input"));
    clear.click();

    expect(input.value).toBe("");
    expect(alphaRow.classList.contains("hidden")).toBe(false);
    expect(betaRow.classList.contains("hidden")).toBe(false);
    expect(clear.classList.contains("hidden")).toBe(true);
  });
});
