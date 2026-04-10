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

  test("platform package headers sort the targeted tbody only", () => {
    document.body.innerHTML = `
      <table>
        <thead>
          <tr>
            <th data-sort-col="0">Route</th>
          </tr>
        </thead>
        <tbody>
          <tr id="row-zeta"><td>zeta route</td></tr>
          <tr id="row-alpha"><td>alpha route</td></tr>
        </tbody>
      </table>
      <table>
        <thead>
          <tr>
            <th data-sort-col="0" data-sort-target="platform-packages-body">Name</th>
            <th>Specifier</th>
            <th>Installed Version</th>
            <th>Latest on PyPI</th>
            <th>Installed</th>
            <th data-sort-col="5" data-sort-target="platform-packages-body">Source Kind</th>
            <th data-sort-col="6" data-sort-target="platform-packages-body">Source Name</th>
          </tr>
        </thead>
        <tbody id="platform-packages-body">
          <tr><td>mkdocs</td><td></td><td>1.6.0</td><td>1.7.0 Different</td><td>No</td><td>group</td><td>docs</td></tr>
          <tr><td>Django</td><td></td><td>5.2.1</td><td>5.2.1 Latest</td><td>Yes</td><td>runtime</td><td></td></tr>
        </tbody>
      </table>
    `;

    window.UnveilReport.sorting.init();

    document
      .querySelector(
        'th[data-sort-target="platform-packages-body"][data-sort-col="0"]',
      )
      .click();

    const packageRows = Array.from(
      document.querySelectorAll("#platform-packages-body tr"),
    );
    const primaryRows = Array.from(
      document.querySelectorAll("table tbody"),
    )[0].querySelectorAll("tr");

    expect(packageRows[0].children[0].textContent).toBe("Django");
    expect(primaryRows[0].children[0].textContent).toBe("zeta route");
  });
});
