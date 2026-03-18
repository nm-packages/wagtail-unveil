(() => {
  var report = window.UnveilReport;

  function getConfig() {
    return {
      apiUrl: document.body.dataset.apiUrl || "",
      reportKind: document.body.dataset.reportKind || "",
    };
  }

  function getSummaryElements() {
    return {
      total: document.getElementById("report-total"),
      testable: document.getElementById("report-testable"),
      untestable: document.getElementById("report-untestable"),
    };
  }

  function setText(element, value) {
    if (element) {
      element.textContent = value;
    }
  }

  function updateSummary(metadata, fallbackCount) {
    var summary = getSummaryElements();
    var totalCount =
      metadata && typeof metadata.total_count === "number"
        ? metadata.total_count
        : fallbackCount;
    var testableCount =
      metadata && typeof metadata.testable_count === "number"
        ? metadata.testable_count
        : 0;
    var untestableCount =
      metadata && typeof metadata.untestable_count === "number"
        ? metadata.untestable_count
        : 0;

    setText(summary.total, String(totalCount));
    setText(summary.testable, String(testableCount));
    setText(summary.untestable, String(untestableCount));
  }

  function getRequestUrl(item, reportKind) {
    if (reportKind === "backend") {
      return "/" + (item.resolved_route || item.route);
    }

    return item.resolved_url || item.url;
  }

  function createActionCell(item, reportKind) {
    var cell = document.createElement("td");
    var testButton = document.createElement("unveil-test-button");
    var requestUrl = getRequestUrl(item, reportKind);

    if (item.is_testable) {
      var group = document.createElement("span");
      var openButton = document.createElement("unveil-open-button");

      group.className = "btn-group";
      testButton.dataset.url = requestUrl;
      openButton.setAttribute("href", requestUrl);
      group.appendChild(testButton);
      group.appendChild(openButton);
      cell.appendChild(group);
      return cell;
    }

    testButton.setAttribute("disabled", "");
    if (item.skip_reason) {
      testButton.setAttribute("title", item.skip_reason);
    }
    cell.appendChild(testButton);
    return cell;
  }

  function createStatusCell(item) {
    var cell = document.createElement("td");

    cell.className = "status-cell";
    if (!item.is_testable && item.skip_reason) {
      var reason = document.createElement("span");
      reason.className = "skip-reason";
      reason.textContent = item.skip_reason;
      cell.appendChild(reason);
      return cell;
    }

    cell.textContent = "\u2014";
    return cell;
  }

  function createTextCell(text, className, tagName) {
    var cell = document.createElement("td");
    var content;

    if (className) {
      cell.className = className;
    }

    if (tagName) {
      content = document.createElement(tagName);
      content.textContent = text || "";
      cell.appendChild(content);
      return cell;
    }

    cell.textContent = text || "";
    return cell;
  }

  function createBackendRow(item) {
    var row = document.createElement("tr");
    var routeLabel =
      item.route.indexOf("admin/") === 0 ? item.route.slice(6) : item.route;

    row.dataset.hasParameters = item.has_parameters ? "true" : "false";
    if (!item.is_testable) {
      row.classList.add("untestable");
    }

    row.appendChild(createTextCell(routeLabel, "route"));
    row.appendChild(createTextCell(item.name));
    row.appendChild(createTextCell(item.namespace));
    row.appendChild(createTextCell(item.view_name, "view", "small"));
    row.appendChild(createActionCell(item, "backend"));
    row.appendChild(createStatusCell(item));
    return row;
  }

  function createFrontendRow(item) {
    var row = document.createElement("tr");

    row.dataset.source = item.source || "";
    if (!item.is_testable) {
      row.classList.add("untestable");
    }

    row.appendChild(createTextCell(item.url, "route"));
    row.appendChild(createTextCell(item.source));
    row.appendChild(createTextCell(item.page_type));
    row.appendChild(createTextCell(item.page_title));
    row.appendChild(createTextCell(item.name));
    row.appendChild(createActionCell(item, "frontend"));
    row.appendChild(createStatusCell(item));
    return row;
  }

  function createEmptyRow(reportKind) {
    var row = document.createElement("tr");
    var cell = document.createElement("td");

    row.className = "empty-row";
    cell.setAttribute("colspan", reportKind === "backend" ? "6" : "7");
    cell.textContent = "No URLs found.";
    row.appendChild(cell);
    return row;
  }

  function renderRows(urls, reportKind) {
    var tbody = report.helpers.getTableBody();

    tbody.innerHTML = "";

    if (!urls.length) {
      tbody.appendChild(createEmptyRow(reportKind));
      return;
    }

    urls.forEach((item) => {
      if (reportKind === "backend") {
        tbody.appendChild(createBackendRow(item));
        return;
      }

      tbody.appendChild(createFrontendRow(item));
    });
  }

  function extractErrorMessage(response, data) {
    if (data && data.error) {
      return data.error;
    }

    return "Report data request failed (" + response.status + ").";
  }

  function loadReportData() {
    var config = getConfig();

    if (!config.apiUrl || !config.reportKind) {
      return Promise.reject(new Error("Report configuration is missing."));
    }

    return fetch(config.apiUrl, {
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    })
      .then((response) =>
        response
          .json()
          .catch(() => {
            throw new Error("Report data response was not valid JSON.");
          })
          .then((data) => {
            if (!response.ok) {
              throw new Error(extractErrorMessage(response, data));
            }

            if (!data || !Array.isArray(data.urls)) {
              throw new Error("Report data response was not valid JSON.");
            }

            return data;
          }),
      )
      .then((data) => {
        var urls = Array.isArray(data.urls) ? data.urls : [];

        updateSummary(data.metadata || null, data.count || urls.length);
        renderRows(urls, config.reportKind);
        return data;
      })
      .catch((error) => {
        updateSummary(null, 0);
        report.helpers.getTableBody().innerHTML = "";
        throw error;
      });
  }

  report.data = {
    loadReportData: loadReportData,
  };
})();
