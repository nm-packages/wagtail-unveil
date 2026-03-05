import { beforeEach, describe, expect, test } from "vitest";

import { loadSourceScripts, resetReportDom } from "./helpers/reportHarness.js";

describe("report components", () => {
  beforeEach(() => {
    resetReportDom();
    loadSourceScripts();
    window.UnveilReport.components.defineCustomElements();
  });

  test("renders filter controls from custom elements", () => {
    expect(document.querySelector(".search-input")).toBeTruthy();
    expect(document.querySelector(".toggle-untestable-btn")).toBeTruthy();
    expect(document.querySelector(".test-all-btn")).toBeTruthy();
    expect(document.querySelector(".pause-btn")).toBeTruthy();
    expect(document.querySelector(".cancel-btn")).toBeTruthy();
    expect(document.querySelector(".help-btn")).toBeTruthy();
    expect(document.querySelector(".reset-btn")).toBeTruthy();
  });

  test("renders standalone test/open actions", () => {
    const testButtonElement = document.createElement("unveil-test-button");
    const openButtonElement = document.createElement("unveil-open-button");

    testButtonElement.dataset.url = "/preview/";
    openButtonElement.setAttribute("href", "/preview/");
    document.body.appendChild(testButtonElement);
    document.body.appendChild(openButtonElement);

    const testButton = testButtonElement.querySelector("button");
    const openButton = openButtonElement.querySelector("a");

    expect(testButton).toBeTruthy();
    expect(testButton.dataset.url).toBe("/preview/");
    expect(openButton).toBeTruthy();
    expect(openButton.getAttribute("href")).toBe("/preview/");
  });
});
