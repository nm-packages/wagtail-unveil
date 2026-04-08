(() => {
  var report = window.UnveilReport;
  var PYPI_LOOKUP_CONCURRENCY = 4;

  function setPlatformPypiButtonState(options) {
    var button = document.getElementById("platform-pypi-lookup-button");
    var isLoading =
      options && typeof options.isLoading === "boolean"
        ? options.isLoading
        : false;
    var label =
      options && typeof options.label === "string"
        ? options.label
        : "Fetch Latest PyPI Versions";

    if (!button) {
      return;
    }

    button.disabled = isLoading;
    button.textContent = label;
  }

  function setSummaryValue(id, value) {
    var element = document.getElementById(id);

    if (element) {
      element.textContent = String(value);
    }
  }

  function updateSummary(metadata, fallbackCount) {
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

    setSummaryValue("report-total", totalCount);
    setSummaryValue("report-testable", testableCount);
    setSummaryValue("report-untestable", untestableCount);
  }

  function updatePlatformSummary(packages, warnings) {
    var installedCount = packages.filter((item) => item.is_installed).length;

    setSummaryValue("report-total", packages.length);
    setSummaryValue("report-testable", installedCount);
    setSummaryValue("report-untestable", packages.length - installedCount);
    setSummaryValue("report-warning-count", warnings.length);
  }

  function createActionCell(item, reportKind) {
    var cell = document.createElement("td");
    var testButton = document.createElement("unveil-test-button");
    var requestUrl;

    if (reportKind === "backend") {
      requestUrl = "/" + (item.resolved_route || item.route);
    } else {
      var queryParams = item.query_params || {};
      var encodedParams = new URLSearchParams(queryParams).toString();

      requestUrl = item.resolved_url || item.url;
      if (encodedParams) {
        requestUrl +=
          requestUrl.indexOf("?") === -1
            ? "?" + encodedParams
            : "&" + encodedParams;
      }
    }

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

  function createPypiLookupCell() {
    var cell = document.createElement("td");
    var value = document.createElement("span");
    var marker = document.createElement("small");

    cell.className = "platform-pypi-cell";
    value.className = "platform-pypi-version";
    value.textContent = "\u2014";
    marker.className = "platform-pypi-status";
    marker.textContent = "";
    cell.appendChild(value);
    cell.appendChild(document.createTextNode(" "));
    cell.appendChild(marker);
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
    row.appendChild(createTextCell(item.page_type));
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

  function renderRows(urls, reportKind) {
    var tbody = report.helpers.getTableBody();

    tbody.innerHTML = "";

    if (!urls.length) {
      var row = document.createElement("tr");
      var cell = document.createElement("td");

      row.className = "empty-row";
      cell.setAttribute("colspan", "7");
      cell.textContent = "No URLs found.";
      row.appendChild(cell);
      tbody.appendChild(row);
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

  function buildReportRequestHeaders(reportAccessToken) {
    var headers = {
      Accept: "application/json",
    };

    if (reportAccessToken) {
      headers["X-Wagtail-Unveil-Report-Access"] = reportAccessToken;
    }

    return headers;
  }

  function getPlatformSectionBody(id) {
    return document.getElementById(id);
  }

  function clearPlatformSections() {
    [
      "platform-runtime-body",
      "platform-source-body",
      "platform-warnings-body",
      "platform-packages-body",
      "platform-metadata-body",
    ].forEach((id) => {
      var tbody = getPlatformSectionBody(id);

      if (tbody) {
        tbody.innerHTML = "";
      }
    });
  }

  function createPlatformRow(label, value) {
    var row = document.createElement("tr");

    row.appendChild(createTextCell(label));
    row.appendChild(createTextCell(value));
    return row;
  }

  function createSingleCellRow(text, colspan) {
    var row = document.createElement("tr");
    var cell = document.createElement("td");

    row.className = "empty-row";
    cell.setAttribute("colspan", String(colspan));
    cell.textContent = text;
    row.appendChild(cell);
    return row;
  }

  function renderPlatformRuntime(runtime) {
    var tbody = getPlatformSectionBody("platform-runtime-body");

    tbody.innerHTML = "";
    tbody.appendChild(
      createPlatformRow("Python Version", runtime.python_version || ""),
    );
    tbody.appendChild(
      createPlatformRow(
        "Python Implementation",
        runtime.python_implementation || "",
      ),
    );
    tbody.appendChild(
      createPlatformRow("Django Version", runtime.django_version || ""),
    );
    tbody.appendChild(
      createPlatformRow("Wagtail Version", runtime.wagtail_version || ""),
    );
  }

  function renderPlatformSource(source) {
    var tbody = getPlatformSectionBody("platform-source-body");

    tbody.innerHTML = "";
    tbody.appendChild(createPlatformRow("Path", source.path || ""));
    tbody.appendChild(createPlatformRow("Format", source.format || ""));
  }

  function renderPlatformWarnings(warnings) {
    var tbody = getPlatformSectionBody("platform-warnings-body");

    tbody.innerHTML = "";
    if (!warnings.length) {
      tbody.appendChild(createSingleCellRow("No warnings.", 1));
      return;
    }

    warnings.forEach((warning) => {
      var row = document.createElement("tr");

      row.appendChild(createTextCell(warning));
      tbody.appendChild(row);
    });
  }

  function renderPlatformPackages(packages) {
    var tbody = getPlatformSectionBody("platform-packages-body");

    tbody.innerHTML = "";
    if (!packages.length) {
      tbody.appendChild(createSingleCellRow("No dependencies found.", 7));
      return;
    }

    packages.forEach((item) => {
      var row = document.createElement("tr");

      row.appendChild(createTextCell(item.name || ""));
      row.appendChild(createTextCell(item.specifier || ""));
      row.appendChild(createTextCell(item.installed_version || ""));
      row.appendChild(createPypiLookupCell());
      row.appendChild(createTextCell(item.is_installed ? "Yes" : "No"));
      row.appendChild(createTextCell(item.source_kind || ""));
      row.appendChild(createTextCell(item.source_name || "\u2014"));
      row.dataset.packageName = item.name || "";
      row.dataset.installedVersion = item.installed_version || "";
      tbody.appendChild(row);
    });
  }

  function setPypiLookupCell(row, options) {
    var cell = row.querySelector(".platform-pypi-cell");
    var value = cell ? cell.querySelector(".platform-pypi-version") : null;
    var marker = cell ? cell.querySelector(".platform-pypi-status") : null;

    if (!value || !marker) {
      return;
    }

    value.textContent = options.versionText;
    marker.textContent = options.markerText || "";
  }

  function setPypiLookupRows(packageName, options) {
    document
      .querySelectorAll("#platform-packages-body tr[data-package-name]")
      .forEach((row) => {
        if (row.dataset.packageName === packageName) {
          setPypiLookupCell(row, options);
        }
      });
  }

  function classifyPypiVersion(installedVersion, latestVersion) {
    if (!installedVersion || !latestVersion) {
      return "Unknown";
    }

    if (installedVersion === latestVersion) {
      return "Latest";
    }

    return "Different";
  }

  function fetchLatestPyPiVersion(packageName) {
    return fetch(
      "https://pypi.org/pypi/" + encodeURIComponent(packageName) + "/json",
      {
        headers: {
          Accept: "application/json",
        },
      },
    ).then((response) => {
      if (response.status === 404) {
        return {
          marker: "",
          status: "not_found",
          version: "Not on PyPI",
        };
      }

      if (!response.ok) {
        throw new Error("PyPI lookup failed.");
      }

      return response.json().then((data) => {
        if (
          !data ||
          typeof data !== "object" ||
          !data.info ||
          typeof data.info.version !== "string"
        ) {
          throw new Error("PyPI lookup failed.");
        }

        return {
          marker: "",
          status: "ok",
          version: data.info.version,
        };
      });
    });
  }

  function runWithConcurrency(taskFactories, limit) {
    var results = new Array(taskFactories.length);
    var nextIndex = 0;
    var activeCount = 0;

    return new Promise((resolve) => {
      function startNext() {
        if (nextIndex >= taskFactories.length && activeCount === 0) {
          resolve(results);
          return;
        }

        while (activeCount < limit && nextIndex < taskFactories.length) {
          const taskIndex = nextIndex;

          nextIndex += 1;
          activeCount += 1;

          taskFactories[taskIndex]()
            .then((result) => {
              results[taskIndex] = result;
            })
            .catch((error) => {
              results[taskIndex] = {
                error: error,
              };
            })
            .finally(() => {
              activeCount -= 1;
              startNext();
            });
        }
      }

      startNext();
    });
  }

  function lookupPlatformPyPiVersions() {
    var rows = Array.from(
      document.querySelectorAll(
        "#platform-packages-body tr[data-package-name]",
      ),
    );
    var packageLookupMap = new Map();
    var packageNames;
    var taskFactories;

    if (!rows.length) {
      return Promise.resolve();
    }

    rows.forEach((row) => {
      var packageName = row.dataset.packageName || "";

      if (!packageName || packageLookupMap.has(packageName)) {
        return;
      }

      packageLookupMap.set(packageName, null);
    });

    packageNames = Array.from(packageLookupMap.keys());
    packageNames.forEach((packageName) => {
      setPypiLookupRows(packageName, {
        markerText: "",
        versionText: "Loading\u2026",
      });
    });

    setPlatformPypiButtonState({
      isLoading: true,
      label: "Fetching PyPI Versions\u2026",
    });

    taskFactories = packageNames.map((packageName) => {
      return function taskFactory() {
        return fetchLatestPyPiVersion(packageName)
          .then((result) => {
            packageLookupMap.set(packageName, result);
            return result;
          })
          .catch(() => {
            var failureResult = {
              marker: "",
              status: "failed",
              version: "Lookup failed",
            };

            packageLookupMap.set(packageName, failureResult);
            return failureResult;
          });
      };
    });

    return runWithConcurrency(taskFactories, PYPI_LOOKUP_CONCURRENCY).finally(
      () => {
        rows.forEach((row) => {
          var packageName = row.dataset.packageName || "";
          var result = packageLookupMap.get(packageName);
          var marker;

          if (!result) {
            setPypiLookupCell(row, {
              markerText: "",
              versionText: "Lookup failed",
            });
            return;
          }

          if (result.status === "ok") {
            marker = classifyPypiVersion(
              row.dataset.installedVersion || "",
              result.version,
            );
            setPypiLookupCell(row, {
              markerText: marker,
              versionText: result.version,
            });
            return;
          }

          if (result.status === "not_found") {
            setPypiLookupCell(row, {
              markerText: "",
              versionText: result.version,
            });
            return;
          }

          setPypiLookupCell(row, {
            markerText: "",
            versionText: result.version,
          });
        });

        setPlatformPypiButtonState({
          isLoading: false,
        });
      },
    );
  }

  function bindPlatformPyPiLookup() {
    var button = document.getElementById("platform-pypi-lookup-button");

    if (!button || button.dataset.unveilPypiBound === "true") {
      return;
    }

    button.dataset.unveilPypiBound = "true";
    button.addEventListener("click", () => {
      lookupPlatformPyPiVersions();
    });
  }

  function renderPlatformMetadata(metadata) {
    var tbody = getPlatformSectionBody("platform-metadata-body");
    var lifecycleStatus =
      metadata &&
      metadata.api_lifecycle &&
      typeof metadata.api_lifecycle.status === "string"
        ? metadata.api_lifecycle.status
        : "";

    tbody.innerHTML = "";
    tbody.appendChild(
      createPlatformRow("API Version", metadata.api_version || ""),
    );
    tbody.appendChild(createPlatformRow("Lifecycle Status", lifecycleStatus));
    tbody.appendChild(
      createPlatformRow("Generated At", metadata.generated_at || ""),
    );
    tbody.appendChild(
      createPlatformRow("Package Version", metadata.package_version || ""),
    );
  }

  function renderPlatformSnapshot(data) {
    var platformData = data.platform || {};
    var runtime = platformData.runtime || {};
    var dependencyData = platformData.python_dependencies || {};
    var source = dependencyData.source || {};
    var packages = Array.isArray(dependencyData.packages)
      ? dependencyData.packages
      : [];
    var warnings = Array.isArray(platformData.warnings)
      ? platformData.warnings
      : [];
    var metadata = data.metadata || {};

    updatePlatformSummary(packages, warnings);
    renderPlatformRuntime(runtime);
    renderPlatformSource(source);
    renderPlatformWarnings(warnings);
    renderPlatformPackages(packages);
    renderPlatformMetadata(metadata);
    bindPlatformPyPiLookup();
    setPlatformPypiButtonState({
      isLoading: false,
    });
  }

  function validateResponsePayload(data, reportKind) {
    if (reportKind === "platform") {
      if (
        !data ||
        typeof data !== "object" ||
        typeof data.platform !== "object" ||
        typeof data.metadata !== "object"
      ) {
        throw new Error("Report data response was not valid JSON.");
      }

      return data;
    }

    if (!data || !Array.isArray(data.urls)) {
      throw new Error("Report data response was not valid JSON.");
    }

    return data;
  }
  function loadReportData() {
    var apiUrl = document.body.dataset.apiUrl || "";
    var reportKind = document.body.dataset.reportKind || "";
    var reportAccessToken = document.body.dataset.reportAccessToken || "";

    if (!apiUrl || !reportKind) {
      return Promise.reject(new Error("Report configuration is missing."));
    }

    return fetch(apiUrl, {
      credentials: "include",
      headers: buildReportRequestHeaders(reportAccessToken),
    })
      .then((response) =>
        response
          .json()
          .catch(() => {
            throw new Error("Report data response was not valid JSON.");
          })
          .then((data) => {
            if (!response.ok) {
              throw new Error(
                data && data.error
                  ? data.error
                  : "Report data request failed (" + response.status + ").",
              );
            }

            return validateResponsePayload(data, reportKind);
          }),
      )
      .then((data) => {
        if (reportKind === "platform") {
          renderPlatformSnapshot(data);
          return data;
        }

        var urls = Array.isArray(data.urls) ? data.urls : [];

        updateSummary(data.metadata || null, data.count || urls.length);
        renderRows(urls, reportKind);
        return data;
      })
      .catch((error) => {
        if (reportKind === "platform") {
          updatePlatformSummary([], []);
          clearPlatformSections();
        } else {
          updateSummary(null, 0);
          report.helpers.getTableBody().innerHTML = "";
        }
        throw error;
      });
  }

  report.data = {
    bindPlatformPyPiLookup: bindPlatformPyPiLookup,
    loadReportData: loadReportData,
    lookupPlatformPyPiVersions: lookupPlatformPyPiVersions,
  };
})();
