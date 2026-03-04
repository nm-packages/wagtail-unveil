import { beforeEach, describe, expect, test } from "vitest";

import { loadSourceScripts, resetReportDom } from "./helpers/reportHarness.js";

function getDataRows() {
  return Array.from(document.querySelectorAll("tbody tr")).filter((row) => {
    return (
      !row.classList.contains("empty-row") &&
      !row.classList.contains("success-banner-row")
    );
  });
}

describe("report sorting", () => {
  beforeEach(() => {
    resetReportDom({
      rowsHtml: `
                <tr id="row-beta"><td>beta route</td><td>beta</td></tr>
                <tr id="row-alpha"><td>alpha route</td><td>alpha</td></tr>
            `,
    });
    loadSourceScripts();
    window.UnveilReport.sorting.init();
  });

  test("sortable headers toggle asc then desc", () => {
    const header = document.querySelector('th[data-sort-col="0"]');

    header.click();

    let rows = getDataRows();
    expect(rows[0].children[0].textContent).toBe("alpha route");
    expect(header.getAttribute("data-sort-dir")).toBe("asc");

    header.click();

    rows = getDataRows();
    expect(rows[0].children[0].textContent).toBe("beta route");
    expect(header.getAttribute("data-sort-dir")).toBe("desc");
  });
});
