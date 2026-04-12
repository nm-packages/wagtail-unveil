(() => {
  var report = window.UnveilReport;
  var PYPI_LOOKUP_CONCURRENCY = 4;
  var COPY_BUTTON_RESET_DELAY_MS = 1500;
  var platformSnapshotState = null;
  var platformPypiResults = new Map();
  var platformPypiLookupPromise = null;
  var platformMarkdownCopyFeedbackTimer = null;

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

  function setPlatformMarkdownButtonState(options) {
    var button = document.getElementById("platform-markdown-report-button");
    var isLoading =
      options && typeof options.isLoading === "boolean"
        ? options.isLoading
        : false;
    var label =
      options && typeof options.label === "string"
        ? options.label
        : "Render Markdown Report";

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

    cell.className = "platform-pypi-cell platform-pypi-neutral";
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

  function getPlatformMarkdownPanel() {
    return document.getElementById("platform-markdown-panel");
  }

  function getPlatformMarkdownOutput() {
    return document.getElementById("platform-markdown-output");
  }

  function getPlatformMarkdownCopyButton() {
    return document.getElementById("platform-markdown-copy-button");
  }

  function resetPlatformClientState() {
    platformSnapshotState = null;
    platformPypiResults = new Map();
    platformPypiLookupPromise = null;
  }

  function setPlatformMarkdownCopyButtonState(options) {
    var button = getPlatformMarkdownCopyButton();
    var isDisabled =
      options && typeof options.isDisabled === "boolean"
        ? options.isDisabled
        : false;
    var label =
      options && typeof options.label === "string"
        ? options.label
        : "Copy Markdown";

    if (!button) {
      return;
    }

    button.disabled = isDisabled;
    button.textContent = label;
  }

  function clearPlatformMarkdownCopyFeedbackTimer() {
    if (platformMarkdownCopyFeedbackTimer) {
      window.clearTimeout(platformMarkdownCopyFeedbackTimer);
      platformMarkdownCopyFeedbackTimer = null;
    }
  }

  function showPlatformMarkdownCopyFeedback(label) {
    clearPlatformMarkdownCopyFeedbackTimer();
    setPlatformMarkdownCopyButtonState({
      isDisabled: false,
      label: label,
    });
    platformMarkdownCopyFeedbackTimer = window.setTimeout(() => {
      setPlatformMarkdownCopyButtonState({
        isDisabled: false,
      });
      platformMarkdownCopyFeedbackTimer = null;
    }, COPY_BUTTON_RESET_DELAY_MS);
  }

  function fallbackCopyPlatformMarkdown(textarea) {
    var selectionStart = textarea.selectionStart;
    var selectionEnd = textarea.selectionEnd;
    var activeElement = document.activeElement;
    var didCopy = false;

    textarea.focus();
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);

    try {
      didCopy = document.execCommand("copy");
    } catch (error) {
      didCopy = false;
    }

    textarea.setSelectionRange(selectionStart, selectionEnd);
    if (activeElement && typeof activeElement.focus === "function") {
      activeElement.focus();
    }
    return didCopy;
  }

  function copyPlatformMarkdownToClipboard() {
    var output = getPlatformMarkdownOutput();

    if (!output || !output.value) {
      return Promise.resolve(false);
    }

    if (
      navigator.clipboard &&
      typeof navigator.clipboard.writeText === "function"
    ) {
      return navigator.clipboard
        .writeText(output.value)
        .then(() => true)
        .catch(() => fallbackCopyPlatformMarkdown(output));
    }

    return Promise.resolve(fallbackCopyPlatformMarkdown(output));
  }

  function hidePlatformMarkdownReport() {
    var panel = getPlatformMarkdownPanel();
    var output = getPlatformMarkdownOutput();

    clearPlatformMarkdownCopyFeedbackTimer();
    if (panel) {
      panel.classList.add("hidden");
    }

    if (output) {
      output.value = "";
    }
  }

  function showPlatformMarkdownReport(markdown) {
    var panel = getPlatformMarkdownPanel();
    var output = getPlatformMarkdownOutput();

    if (!panel || !output) {
      return;
    }

    output.value = markdown;
    panel.classList.remove("hidden");
    setPlatformMarkdownCopyButtonState({
      isDisabled: false,
    });
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
    hidePlatformMarkdownReport();
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
      row.dataset.packageLookupName = normalizePypiPackageName(item.name || "");
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

    cell.classList.remove(
      "platform-pypi-neutral",
      "platform-pypi-success",
      "platform-pypi-warning",
      "platform-pypi-danger",
    );
    cell.classList.add(options.toneClass || "platform-pypi-neutral");
    value.textContent = options.versionText;
    marker.textContent = options.markerText || "";
  }

  function normalizePypiPackageName(packageName) {
    return packageName
      .toLowerCase()
      .replace(/[-_.]+/g, "-")
      .trim();
  }

  function setPypiLookupRows(packageLookupName, options) {
    document
      .querySelectorAll("#platform-packages-body tr[data-package-lookup-name]")
      .forEach((row) => {
        if (row.dataset.packageLookupName === packageLookupName) {
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

  function fetchLatestPyPiVersion(packageLookupName) {
    return fetch(
      "https://pypi.org/pypi/" +
        encodeURIComponent(packageLookupName) +
        "/json",
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

  function getPypiResultDisplay(result, installedVersion) {
    var marker = "";

    if (!result) {
      return {
        marker: "",
        version: "\u2014",
      };
    }

    if (result.status === "ok") {
      marker = classifyPypiVersion(installedVersion || "", result.version);
      return {
        marker: marker,
        version: result.version,
      };
    }

    return {
      marker: "",
      version: result.version,
    };
  }

  function applyPypiLookupResult(packageLookupName, result) {
    document
      .querySelectorAll("#platform-packages-body tr[data-package-lookup-name]")
      .forEach((row) => {
        var display;

        if (row.dataset.packageLookupName !== packageLookupName) {
          return;
        }

        if (!result) {
          setPypiLookupCell(row, {
            markerText: "",
            toneClass: "platform-pypi-danger",
            versionText: "Lookup failed",
          });
          return;
        }

        if (result.status === "ok") {
          display = getPypiResultDisplay(
            result,
            row.dataset.installedVersion || "",
          );
          setPypiLookupCell(row, {
            markerText: display.marker,
            toneClass:
              display.marker === "Latest"
                ? "platform-pypi-success"
                : "platform-pypi-warning",
            versionText: display.version,
          });
          return;
        }

        if (result.status === "not_found") {
          setPypiLookupCell(row, {
            markerText: "",
            toneClass: "platform-pypi-danger",
            versionText: result.version,
          });
          return;
        }

        setPypiLookupCell(row, {
          markerText: "",
          toneClass: "platform-pypi-danger",
          versionText: result.version,
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

  function hasCachedPypiResultForAllPackages() {
    var packages = platformSnapshotState && platformSnapshotState.packages;

    if (!Array.isArray(packages) || !packages.length) {
      return true;
    }

    return packages.every((item) => {
      var packageLookupName = normalizePypiPackageName(item.name || "");

      return !packageLookupName || platformPypiResults.has(packageLookupName);
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

    if (platformPypiLookupPromise) {
      return platformPypiLookupPromise;
    }

    rows.forEach((row) => {
      var packageLookupName = row.dataset.packageLookupName || "";

      if (!packageLookupName || packageLookupMap.has(packageLookupName)) {
        return;
      }

      packageLookupMap.set(packageLookupName, null);
    });

    packageNames = Array.from(packageLookupMap.keys());
    packageNames.forEach((packageLookupName) => {
      setPypiLookupRows(packageLookupName, {
        markerText: "",
        toneClass: "platform-pypi-neutral",
        versionText: "Loading\u2026",
      });
    });

    setPlatformPypiButtonState({
      isLoading: true,
      label: "Fetching PyPI Versions\u2026",
    });

    platformPypiLookupPromise = runWithConcurrency(
      packageNames.map((packageLookupName) => {
        return function taskFactory() {
          return fetchLatestPyPiVersion(packageLookupName)
            .then((result) => {
              packageLookupMap.set(packageLookupName, result);
              platformPypiResults.set(packageLookupName, result);
              applyPypiLookupResult(packageLookupName, result);
              return result;
            })
            .catch(() => {
              var failureResult = {
                marker: "",
                status: "failed",
                version: "Lookup failed",
              };

              packageLookupMap.set(packageLookupName, failureResult);
              platformPypiResults.set(packageLookupName, failureResult);
              applyPypiLookupResult(packageLookupName, failureResult);
              return failureResult;
            });
        };
      }),
      PYPI_LOOKUP_CONCURRENCY,
    ).finally(() => {
      platformPypiLookupPromise = null;
      setPlatformPypiButtonState({
        isLoading: false,
      });
    });

    return platformPypiLookupPromise;
  }

  function ensurePlatformPyPiVersionsLoaded() {
    if (platformPypiLookupPromise) {
      return platformPypiLookupPromise;
    }

    if (hasCachedPypiResultForAllPackages()) {
      return Promise.resolve();
    }

    return lookupPlatformPyPiVersions();
  }

  function escapeMarkdownCell(value) {
    return String(value || "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, " ");
  }

  function serializePlatformKeyValueRows(rows) {
    return rows
      .map(([label, value]) => "- " + label + ": " + (value || ""))
      .join("\n");
  }

  function serializePlatformWarnings(warnings) {
    if (!warnings.length) {
      return "No warnings.";
    }

    return warnings.map((warning) => "- " + warning).join("\n");
  }

  function serializePlatformPackages(packages) {
    if (!packages.length) {
      return "No dependencies found.";
    }

    return [
      "| Name | Specifier | Installed Version | Latest on PyPI | Status | Installed | Source Kind | Source Name |",
      "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
      .concat(
        packages.map((item) => {
          var packageLookupName = normalizePypiPackageName(item.name || "");
          var display = getPypiResultDisplay(
            platformPypiResults.get(packageLookupName),
            item.installed_version || "",
          );

          return (
            "| " +
            [
              item.name || "",
              item.specifier || "",
              item.installed_version || "\u2014",
              display.version || "\u2014",
              display.marker || "\u2014",
              item.is_installed ? "Yes" : "No",
              item.source_kind || "",
              item.source_name || "\u2014",
            ]
              .map(escapeMarkdownCell)
              .join(" | ") +
            " |"
          );
        }),
      )
      .join("\n");
  }

  function buildPlatformMarkdownReport() {
    var runtime =
      (platformSnapshotState && platformSnapshotState.runtime) || {};
    var source = (platformSnapshotState && platformSnapshotState.source) || {};
    var warnings =
      (platformSnapshotState && platformSnapshotState.warnings) || [];
    var packages =
      (platformSnapshotState && platformSnapshotState.packages) || [];
    var metadata =
      (platformSnapshotState && platformSnapshotState.metadata) || {};
    var installedCount = packages.filter((item) => item.is_installed).length;
    var lifecycleStatus =
      metadata &&
      metadata.api_lifecycle &&
      typeof metadata.api_lifecycle.status === "string"
        ? metadata.api_lifecycle.status
        : "";

    return [
      "# Platform Report",
      "",
      "Packages: " +
        packages.length +
        " total, " +
        installedCount +
        " installed, " +
        (packages.length - installedCount) +
        " missing, " +
        warnings.length +
        " warnings.",
      "",
      "## Runtime",
      serializePlatformKeyValueRows([
        ["Python Version", runtime.python_version || ""],
        ["Python Implementation", runtime.python_implementation || ""],
        ["Django Version", runtime.django_version || ""],
        ["Wagtail Version", runtime.wagtail_version || ""],
      ]),
      "",
      "## Dependency Source",
      serializePlatformKeyValueRows([
        ["Path", source.path || ""],
        ["Format", source.format || ""],
      ]),
      "",
      "## Warnings",
      serializePlatformWarnings(warnings),
      "",
      "## Python Dependencies",
      serializePlatformPackages(packages),
      "",
      "## Metadata",
      serializePlatformKeyValueRows([
        ["API Version", metadata.api_version || ""],
        ["Lifecycle Status", lifecycleStatus],
        ["Generated At", metadata.generated_at || ""],
        ["Package Version", metadata.package_version || ""],
      ]),
    ].join("\n");
  }

  function renderPlatformMarkdownReport() {
    if (!platformSnapshotState) {
      return Promise.resolve();
    }

    setPlatformMarkdownButtonState({
      isLoading: true,
      label: "Rendering Markdown Report\u2026",
    });

    return ensurePlatformPyPiVersionsLoaded()
      .then(() => {
        showPlatformMarkdownReport(buildPlatformMarkdownReport());
      })
      .finally(() => {
        setPlatformMarkdownButtonState({
          isLoading: false,
        });
      });
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

  function bindPlatformMarkdownReport() {
    var button = document.getElementById("platform-markdown-report-button");

    if (!button || button.dataset.unveilMarkdownBound === "true") {
      return;
    }

    button.dataset.unveilMarkdownBound = "true";
    button.addEventListener("click", () => {
      renderPlatformMarkdownReport();
    });
  }

  function bindPlatformMarkdownCopy() {
    var button = getPlatformMarkdownCopyButton();

    if (!button || button.dataset.unveilMarkdownCopyBound === "true") {
      return;
    }

    button.dataset.unveilMarkdownCopyBound = "true";
    button.addEventListener("click", () => {
      setPlatformMarkdownCopyButtonState({
        isDisabled: true,
        label: "Copying\u2026",
      });
      copyPlatformMarkdownToClipboard().then((didCopy) => {
        showPlatformMarkdownCopyFeedback(didCopy ? "Copied" : "Copy failed");
      });
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

    resetPlatformClientState();
    hidePlatformMarkdownReport();
    platformSnapshotState = {
      metadata: metadata,
      packages: packages,
      runtime: runtime,
      source: source,
      warnings: warnings,
    };
    updatePlatformSummary(packages, warnings);
    renderPlatformRuntime(runtime);
    renderPlatformSource(source);
    renderPlatformWarnings(warnings);
    renderPlatformPackages(packages);
    renderPlatformMetadata(metadata);
    bindPlatformPyPiLookup();
    bindPlatformMarkdownReport();
    bindPlatformMarkdownCopy();
    setPlatformPypiButtonState({
      isLoading: false,
    });
    setPlatformMarkdownButtonState({
      isLoading: false,
    });
    setPlatformMarkdownCopyButtonState({
      isDisabled: false,
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
          resetPlatformClientState();
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
    bindPlatformMarkdownCopy: bindPlatformMarkdownCopy,
    bindPlatformMarkdownReport: bindPlatformMarkdownReport,
    bindPlatformPyPiLookup: bindPlatformPyPiLookup,
    buildPlatformMarkdownReport: buildPlatformMarkdownReport,
    ensurePlatformPyPiVersionsLoaded: ensurePlatformPyPiVersionsLoaded,
    loadReportData: loadReportData,
    lookupPlatformPyPiVersions: lookupPlatformPyPiVersions,
    renderPlatformMarkdownReport: renderPlatformMarkdownReport,
  };
})();
