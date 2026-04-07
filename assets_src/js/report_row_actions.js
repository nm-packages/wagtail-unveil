(() => {
  var report = window.UnveilReport;
  var helpers = report.helpers;

  function finalizeResult(button, row, statusCell, result, options) {
    helpers.renderStatus(statusCell, result.statusClass, result.label);
    button.disabled = false;
    button.textContent = "Test";

    if (!options || options.moveFailedRow !== false) {
      helpers.moveFailedRowToTop(row, result.statusClass);
    }

    if (options && typeof options.onComplete === "function") {
      options.onComplete(result, row, button);
    }

    return result;
  }

  function testUrlButton(button, options) {
    var url;
    var row;
    var statusCell;

    if (!button || !button.dataset.url) {
      return Promise.resolve(null);
    }

    url = button.dataset.url;
    row = button.closest("tr");
    statusCell = button.closest("td").nextElementSibling;

    button.disabled = true;
    button.textContent = "\u2026";
    statusCell.innerHTML = "\u2014";

    return fetch(url, { credentials: "include" })
      .then((response) =>
        finalizeResult(
          button,
          row,
          statusCell,
          {
            code: response.status,
            label: String(response.status),
            statusClass: helpers.classifyStatus(response.status),
          },
          options,
        ),
      )
      .catch(() =>
        finalizeResult(
          button,
          row,
          statusCell,
          {
            code: null,
            label: "ERR",
            statusClass: "status-err",
          },
          options,
        ),
      );
  }

  report.rowActions = {
    testUrlButton: testUrlButton,
  };
})();
