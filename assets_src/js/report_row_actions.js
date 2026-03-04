(() => {
  var report = window.UnveilReport;
  var helpers = report.helpers;

  function setBusyState(button) {
    button.disabled = true;
    button.textContent = "\u2026";
  }

  function resetBusyState(button) {
    button.disabled = false;
    button.textContent = "Test";
  }

  function finalizeResult(button, row, statusCell, result, options) {
    helpers.renderStatus(statusCell, result.statusClass, result.label);
    resetBusyState(button);

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

    setBusyState(button);
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
