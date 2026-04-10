(() => {
  // assets_src/js/report_core.js
  (() => {
    if (window.UnveilReport) {
      return;
    }
    function getCookieFlag(name) {
      var match = document.cookie.match(
        new RegExp("(?:^|; )" + name + "=([^;]*)")
      );
      return match ? match[1] === "1" : false;
    }
    function setCookieFlag(name, enabled) {
      document.cookie = name + "=" + (enabled ? "1" : "0") + "; path=/; max-age=31536000";
    }
    function getTableBody() {
      return document.querySelector("tbody");
    }
    function isDataRow(row) {
      return !row.classList.contains("empty-row") && !row.classList.contains("success-banner-row");
    }
    function clearSuccessBanner() {
      var banner = document.querySelector("tbody .success-banner-row");
      if (banner) {
        banner.remove();
      }
    }
    function clearLoadingFeedbackTimer() {
      if (window.UnveilReport && window.UnveilReport.state.loadingFeedbackTimer) {
        window.clearTimeout(window.UnveilReport.state.loadingFeedbackTimer);
        window.UnveilReport.state.loadingFeedbackTimer = null;
      }
    }
    function setLoadingFeedbackVisibility(visible) {
      document.body.dataset.loadingFeedback = visible ? "visible" : "hidden";
    }
    function setPageState(state) {
      if (state !== "loading") {
        clearLoadingFeedbackTimer();
        setLoadingFeedbackVisibility(false);
      }
      document.body.dataset.reportState = state;
    }
    function showLoadingScreen(message, options) {
      var loadingMessage = document.getElementById("report-loading-message");
      var errorMessage = document.getElementById("report-error-message");
      var delayMs = options && typeof options.delayMs === "number" ? options.delayMs : 0;
      if (loadingMessage) {
        loadingMessage.textContent = message;
      }
      if (errorMessage) {
        errorMessage.textContent = "";
      }
      setPageState("loading");
      clearLoadingFeedbackTimer();
      if (delayMs > 0) {
        setLoadingFeedbackVisibility(false);
        window.UnveilReport.state.loadingFeedbackTimer = window.setTimeout(() => {
          if (document.body.dataset.reportState === "loading") {
            setLoadingFeedbackVisibility(true);
          }
          window.UnveilReport.state.loadingFeedbackTimer = null;
        }, delayMs);
        return;
      }
      setLoadingFeedbackVisibility(true);
    }
    function showErrorScreen(message) {
      var errorMessage = document.getElementById("report-error-message");
      if (errorMessage) {
        errorMessage.textContent = message;
      }
      setPageState("error");
    }
    function getVisibleTestButtons() {
      return Array.from(
        document.querySelectorAll(
          "tbody tr:not(.hidden) .test-btn:not(:disabled)"
        )
      );
    }
    function classifyStatus(code) {
      if (code >= 200 && code < 300) {
        return "status-2xx";
      }
      if (code >= 300 && code < 400) {
        return "status-3xx";
      }
      if (code >= 400 && code < 500) {
        return "status-4xx";
      }
      if (code >= 500) {
        return "status-5xx";
      }
      return "status-err";
    }
    function renderStatus(statusCell, statusClass, label) {
      statusCell.innerHTML = '<span class="status ' + statusClass + '">' + label + "</span>";
    }
    function moveFailedRowToTop(row, statusClass) {
      if (statusClass !== "status-2xx") {
        row.closest("tbody").prepend(row);
      }
    }
    window.UnveilReport = {
      state: {
        currentSearchTerm: "",
        currentSortCol: null,
        currentSortAsc: true,
        hideUntestable: getCookieFlag("unveil_hide_untestable"),
        loadingFeedbackTimer: null,
        testState: null
      },
      helpers: {
        classifyStatus,
        clearLoadingFeedbackTimer,
        clearSuccessBanner,
        getTableBody,
        getVisibleTestButtons,
        isDataRow,
        moveFailedRowToTop,
        renderStatus,
        setLoadingFeedbackVisibility,
        setPageState,
        setCookieFlag,
        showErrorScreen,
        showLoadingScreen
      }
    };
  })();

  // assets_src/js/report_filters.js
  (() => {
    var report = window.UnveilReport;
    var state = report.state;
    var helpers = report.helpers;
    function rowMatchesSearch(row) {
      var searchTerm = state.currentSearchTerm;
      var sortableCols;
      var index;
      var colIdx;
      var text;
      if (!helpers.isDataRow(row)) {
        return true;
      }
      if (!searchTerm) {
        return true;
      }
      sortableCols = document.querySelectorAll("th[data-sort-col]");
      for (index = 0; index < sortableCols.length; index++) {
        colIdx = Number.parseInt(
          sortableCols[index].getAttribute("data-sort-col"),
          10
        );
        text = row.children[colIdx].textContent.toLowerCase();
        if (text.indexOf(searchTerm) !== -1) {
          return true;
        }
      }
      return false;
    }
    function applyFilters() {
      document.querySelectorAll("tbody tr").forEach((row) => {
        var visible = rowMatchesSearch(row);
        if (visible && helpers.isDataRow(row) && state.hideUntestable && row.classList.contains("untestable")) {
          visible = false;
        }
        row.classList.toggle("hidden", !visible);
      });
    }
    function syncUntestableButton() {
      var button = document.querySelector(".toggle-untestable-btn");
      if (!button) {
        return;
      }
      button.textContent = state.hideUntestable ? "Show Untestable" : "Hide Untestable";
      button.classList.toggle("active", state.hideUntestable);
    }
    function toggleUntestable() {
      state.hideUntestable = !state.hideUntestable;
      helpers.setCookieFlag("unveil_hide_untestable", state.hideUntestable);
      syncUntestableButton();
      applyFilters();
    }
    function updateSearchTerm(value) {
      state.currentSearchTerm = value.toLowerCase();
      helpers.clearSuccessBanner();
      applyFilters();
    }
    function init() {
      syncUntestableButton();
      if (state.hideUntestable) {
        applyFilters();
      }
    }
    report.filters = {
      applyFilters,
      init,
      syncUntestableButton,
      toggleUntestable,
      updateSearchTerm
    };
  })();

  // assets_src/js/report_sorting.js
  (() => {
    var report = window.UnveilReport;
    var helpers = report.helpers;
    var state = report.state;
    function getTargetTableBody(header) {
      var targetId = header.dataset.sortTarget;
      if (targetId) {
        return document.getElementById(targetId);
      }
      return header.closest("table").querySelector("tbody");
    }
    function sortRowsByColumn(col, tbody) {
      var rows = Array.from(tbody.querySelectorAll("tr"));
      var structuralRows = [];
      var dataRows = [];
      rows.forEach((row) => {
        if (helpers.isDataRow(row)) {
          dataRows.push(row);
          return;
        }
        structuralRows.push(row);
      });
      dataRows.sort((a, b) => {
        var aText = a.children[col].textContent.toLowerCase();
        var bText = b.children[col].textContent.toLowerCase();
        if (aText < bText) {
          return state.currentSortAsc ? -1 : 1;
        }
        if (aText > bText) {
          return state.currentSortAsc ? 1 : -1;
        }
        return 0;
      });
      tbody.innerHTML = "";
      structuralRows.concat(dataRows).forEach((row) => {
        tbody.appendChild(row);
      });
    }
    function updateSortIndicators(activeHeader) {
      var targetId = activeHeader.dataset.sortTarget || "";
      document.querySelectorAll("th[data-sort-col]").forEach((header) => {
        if ((header.dataset.sortTarget || "") !== targetId) {
          return;
        }
        header.removeAttribute("data-sort-dir");
      });
      activeHeader.setAttribute(
        "data-sort-dir",
        state.currentSortAsc ? "asc" : "desc"
      );
    }
    function handleSortClick(event) {
      var header = event.currentTarget;
      var col = Number.parseInt(header.getAttribute("data-sort-col"), 10);
      var targetId = header.dataset.sortTarget || "";
      var tbody = getTargetTableBody(header);
      if (state.currentSortCol === col && state.currentSortTarget === targetId) {
        state.currentSortAsc = !state.currentSortAsc;
      } else {
        state.currentSortCol = col;
        state.currentSortTarget = targetId;
        state.currentSortAsc = true;
      }
      updateSortIndicators(header);
      sortRowsByColumn(col, tbody);
    }
    function init() {
      document.querySelectorAll("th[data-sort-col]").forEach((header) => {
        if (header.dataset.unveilSortBound === "true") {
          return;
        }
        header.dataset.unveilSortBound = "true";
        header.addEventListener("click", handleSortClick);
      });
    }
    report.sorting = {
      init
    };
  })();

  // assets_src/js/report_row_actions.js
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
      return fetch(url, { credentials: "include" }).then(
        (response) => finalizeResult(
          button,
          row,
          statusCell,
          {
            code: response.status,
            label: String(response.status),
            statusClass: helpers.classifyStatus(response.status)
          },
          options
        )
      ).catch(
        () => finalizeResult(
          button,
          row,
          statusCell,
          {
            code: null,
            label: "ERR",
            statusClass: "status-err"
          },
          options
        )
      );
    }
    report.rowActions = {
      testUrlButton
    };
  })();

  // assets_src/js/report_batch_runner.js
  (() => {
    var report = window.UnveilReport;
    var helpers = report.helpers;
    var state = report.state;
    var RUN_STATUS_FINISHED = "finished";
    var RUN_STATUS_RUNNING = "running";
    var RUN_STATUS_PAUSED = "paused";
    var RUN_STATUS_STOPPED = "stopped";
    function getControls() {
      return {
        cancelButton: document.querySelector(".cancel-btn"),
        pauseButton: document.querySelector(".pause-btn"),
        summary: document.getElementById("test-all-summary"),
        testAllButton: document.querySelector(".test-all-btn")
      };
    }
    function finishTests() {
      var controls = getControls();
      var runState = state.testState;
      var tbody;
      var banner;
      var bannerCell;
      if (!runState) {
        return;
      }
      runState.status = RUN_STATUS_FINISHED;
      controls.testAllButton.classList.remove("hidden");
      controls.pauseButton.classList.add("hidden");
      controls.cancelButton.classList.add("hidden");
      runState.summaryEl.innerHTML = 'Results: <span class="pass">' + runState.passed + ' passed</span>, <span class="fail">' + runState.failed + " failed</span> out of " + runState.done + "/" + runState.total;
      state.testState = null;
      if (runState.failed === 0 && runState.total > 0) {
        tbody = helpers.getTableBody();
        banner = document.createElement("tr");
        banner.className = "success-banner-row";
        bannerCell = document.createElement("td");
        bannerCell.setAttribute("colspan", "100");
        bannerCell.innerHTML = "&#10003; All " + runState.total + " URLs returned 2xx \u2014 no errors found.";
        banner.appendChild(bannerCell);
        tbody.prepend(banner);
      }
      controls.pauseButton.textContent = "Pause";
    }
    function updateSummary() {
      var controls = getControls();
      var runState = state.testState;
      if (!runState) {
        return;
      }
      if (runState.done >= runState.total) {
        finishTests();
        return;
      }
      if (runState.status === RUN_STATUS_PAUSED) {
        controls.pauseButton.textContent = "Continue";
        runState.summaryEl.innerHTML = "Paused: " + runState.done + "/" + runState.total;
        return;
      }
      controls.pauseButton.textContent = "Pause (" + runState.done + "/" + runState.total + ")";
      runState.summaryEl.innerHTML = "Progress: " + runState.done + "/" + runState.total;
    }
    function runNext(index) {
      var runState = state.testState;
      if (!runState) {
        return;
      }
      if (runState.status === RUN_STATUS_PAUSED) {
        runState.nextIndex = index;
        return;
      }
      if (runState.status === RUN_STATUS_STOPPED) {
        return;
      }
      if (index >= runState.buttons.length) {
        finishTests();
        return;
      }
      runState.nextIndex = index;
      report.rowActions.testUrlButton(runState.buttons[index], {
        onComplete: (result) => {
          if (result.statusClass === "status-2xx") {
            runState.passed += 1;
          } else {
            runState.failed += 1;
          }
          runState.done += 1;
          updateSummary();
          if (state.testState) {
            window.setTimeout(() => {
              runNext(index + 1);
            }, 100);
          }
        }
      });
    }
    function pauseTests() {
      var controls = getControls();
      var runState = state.testState;
      if (!runState) {
        return;
      }
      if (runState.status !== RUN_STATUS_RUNNING) {
        return;
      }
      runState.status = RUN_STATUS_PAUSED;
      controls.pauseButton.textContent = "Continue";
      controls.cancelButton.classList.remove("hidden");
      runState.summaryEl.innerHTML = "Paused: " + runState.done + "/" + runState.total;
    }
    function continueTests() {
      var controls = getControls();
      var runState = state.testState;
      if (!runState) {
        return;
      }
      if (runState.status !== RUN_STATUS_PAUSED) {
        return;
      }
      runState.status = RUN_STATUS_RUNNING;
      controls.pauseButton.textContent = "Pause";
      controls.cancelButton.classList.add("hidden");
      runNext(runState.nextIndex);
    }
    function handlePauseClick() {
      var runState = state.testState;
      if (!runState) {
        return;
      }
      if (runState.status === RUN_STATUS_PAUSED) {
        continueTests();
        return;
      }
      if (runState.status === RUN_STATUS_RUNNING) {
        pauseTests();
      }
    }
    function cancelTests() {
      var runState = state.testState;
      if (runState) {
        runState.status = RUN_STATUS_STOPPED;
        state.testState = null;
      }
      window.location.reload();
    }
    function testAll() {
      var controls = getControls();
      var buttons = helpers.getVisibleTestButtons();
      if (buttons.length === 0) {
        return;
      }
      controls.testAllButton.classList.add("hidden");
      controls.pauseButton.classList.remove("hidden");
      controls.cancelButton.classList.add("hidden");
      controls.summary.classList.remove("hidden");
      controls.pauseButton.textContent = "Pause";
      helpers.clearSuccessBanner();
      document.querySelectorAll("tbody tr:not(.hidden):not(.untestable) .status-cell").forEach((cell) => {
        cell.innerHTML = "\u2014";
      });
      state.testState = {
        buttons,
        done: 0,
        failed: 0,
        nextIndex: 0,
        passed: 0,
        summaryEl: controls.summary,
        status: RUN_STATUS_RUNNING,
        total: buttons.length
      };
      updateSummary();
      runNext(0);
    }
    report.batchRunner = {
      cancelTests,
      continueTests,
      handlePauseClick,
      pauseTests,
      testAll
    };
  })();

  // assets_src/js/report_components.js
  (() => {
    var report = window.UnveilReport;
    class UnveilResetButton extends HTMLElement {
      connectedCallback() {
        var button;
        if (this.querySelector("button")) {
          return;
        }
        button = document.createElement("button");
        button.type = "button";
        button.className = "reset-btn";
        button.textContent = "Reset";
        button.addEventListener("click", () => {
          window.location.reload();
        });
        this.appendChild(button);
      }
    }
    class UnveilToggleUntestableButton extends HTMLElement {
      connectedCallback() {
        var button;
        if (this.querySelector("button")) {
          return;
        }
        button = document.createElement("button");
        button.type = "button";
        button.className = "toggle-untestable-btn";
        button.addEventListener("click", report.filters.toggleUntestable);
        this.appendChild(button);
      }
    }
    class UnveilTestAllButton extends HTMLElement {
      connectedCallback() {
        var button;
        if (this.querySelector("button")) {
          return;
        }
        button = document.createElement("button");
        button.type = "button";
        button.className = "test-all-btn";
        button.textContent = "Test All";
        button.addEventListener("click", report.batchRunner.testAll);
        this.appendChild(button);
      }
    }
    class UnveilPauseButton extends HTMLElement {
      connectedCallback() {
        var button;
        if (this.querySelector("button")) {
          return;
        }
        button = document.createElement("button");
        button.type = "button";
        button.className = "pause-btn hidden";
        button.textContent = "Pause";
        button.addEventListener("click", report.batchRunner.handlePauseClick);
        this.appendChild(button);
      }
    }
    class UnveilCancelButton extends HTMLElement {
      connectedCallback() {
        var button;
        if (this.querySelector("button")) {
          return;
        }
        button = document.createElement("button");
        button.type = "button";
        button.className = "cancel-btn hidden";
        button.textContent = "Cancel";
        button.addEventListener("click", report.batchRunner.cancelTests);
        this.appendChild(button);
      }
    }
    class UnveilSearchInput extends HTMLElement {
      connectedCallback() {
        var wrapper;
        var input;
        var clear;
        if (this.querySelector("input")) {
          return;
        }
        wrapper = document.createElement("div");
        wrapper.className = "search-wrapper";
        input = document.createElement("input");
        input.type = "text";
        input.className = "search-input";
        input.placeholder = this.getAttribute("placeholder") || "";
        clear = document.createElement("button");
        clear.type = "button";
        clear.className = "search-clear hidden";
        clear.setAttribute("aria-label", "Clear search");
        clear.textContent = "\xD7";
        input.addEventListener("input", () => {
          clear.classList.toggle("hidden", !input.value);
          report.filters.updateSearchTerm(input.value);
        });
        clear.addEventListener("click", () => {
          input.value = "";
          clear.classList.add("hidden");
          report.filters.updateSearchTerm("");
        });
        wrapper.appendChild(input);
        wrapper.appendChild(clear);
        this.appendChild(wrapper);
      }
    }
    class UnveilTestButton extends HTMLElement {
      connectedCallback() {
        var button;
        var title;
        var url;
        if (this.querySelector("button")) {
          return;
        }
        button = document.createElement("button");
        button.type = "button";
        button.className = "test-btn";
        button.textContent = "Test";
        url = this.dataset.url;
        if (url) {
          button.dataset.url = url;
          button.addEventListener("click", () => {
            report.rowActions.testUrlButton(button);
          });
        } else {
          button.disabled = true;
        }
        if (this.hasAttribute("disabled")) {
          button.disabled = true;
        }
        title = this.getAttribute("title");
        if (title) {
          button.title = title;
        }
        this.appendChild(button);
      }
    }
    class UnveilOpenButton extends HTMLElement {
      connectedCallback() {
        var link;
        var href;
        if (this.querySelector("a")) {
          return;
        }
        link = document.createElement("a");
        link.className = "open-btn";
        link.textContent = "Open";
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        href = this.getAttribute("href");
        if (href) {
          link.href = href;
        }
        this.appendChild(link);
      }
    }
    function defineCustomElements() {
      [
        ["unveil-reset-button", UnveilResetButton],
        ["unveil-toggle-untestable-button", UnveilToggleUntestableButton],
        ["unveil-test-all-button", UnveilTestAllButton],
        ["unveil-pause-button", UnveilPauseButton],
        ["unveil-cancel-button", UnveilCancelButton],
        ["unveil-search-input", UnveilSearchInput],
        ["unveil-test-button", UnveilTestButton],
        ["unveil-open-button", UnveilOpenButton]
      ].forEach(([name, constructor]) => {
        if (!customElements.get(name)) {
          customElements.define(name, constructor);
        }
      });
    }
    report.components = {
      defineCustomElements
    };
  })();

  // assets_src/js/report_data.js
  (() => {
    var report = window.UnveilReport;
    var PYPI_LOOKUP_CONCURRENCY = 4;
    function setPlatformPypiButtonState(options) {
      var button = document.getElementById("platform-pypi-lookup-button");
      var isLoading = options && typeof options.isLoading === "boolean" ? options.isLoading : false;
      var label = options && typeof options.label === "string" ? options.label : "Fetch Latest PyPI Versions";
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
      var totalCount = metadata && typeof metadata.total_count === "number" ? metadata.total_count : fallbackCount;
      var testableCount = metadata && typeof metadata.testable_count === "number" ? metadata.testable_count : 0;
      var untestableCount = metadata && typeof metadata.untestable_count === "number" ? metadata.untestable_count : 0;
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
          requestUrl += requestUrl.indexOf("?") === -1 ? "?" + encodedParams : "&" + encodedParams;
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
      var routeLabel = item.route.indexOf("admin/") === 0 ? item.route.slice(6) : item.route;
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
        Accept: "application/json"
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
        "platform-metadata-body"
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
        createPlatformRow("Python Version", runtime.python_version || "")
      );
      tbody.appendChild(
        createPlatformRow(
          "Python Implementation",
          runtime.python_implementation || ""
        )
      );
      tbody.appendChild(
        createPlatformRow("Django Version", runtime.django_version || "")
      );
      tbody.appendChild(
        createPlatformRow("Wagtail Version", runtime.wagtail_version || "")
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
        "platform-pypi-danger"
      );
      cell.classList.add(options.toneClass || "platform-pypi-neutral");
      value.textContent = options.versionText;
      marker.textContent = options.markerText || "";
    }
    function normalizePypiPackageName(packageName) {
      return packageName.toLowerCase().replace(/[-_.]+/g, "-").trim();
    }
    function setPypiLookupRows(packageLookupName, options) {
      document.querySelectorAll("#platform-packages-body tr[data-package-lookup-name]").forEach((row) => {
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
        "https://pypi.org/pypi/" + encodeURIComponent(packageLookupName) + "/json",
        {
          headers: {
            Accept: "application/json"
          }
        }
      ).then((response) => {
        if (response.status === 404) {
          return {
            marker: "",
            status: "not_found",
            version: "Not on PyPI"
          };
        }
        if (!response.ok) {
          throw new Error("PyPI lookup failed.");
        }
        return response.json().then((data) => {
          if (!data || typeof data !== "object" || !data.info || typeof data.info.version !== "string") {
            throw new Error("PyPI lookup failed.");
          }
          return {
            marker: "",
            status: "ok",
            version: data.info.version
          };
        });
      });
    }
    function applyPypiLookupResult(packageLookupName, result) {
      document.querySelectorAll("#platform-packages-body tr[data-package-lookup-name]").forEach((row) => {
        var marker;
        if (row.dataset.packageLookupName !== packageLookupName) {
          return;
        }
        if (!result) {
          setPypiLookupCell(row, {
            markerText: "",
            toneClass: "platform-pypi-danger",
            versionText: "Lookup failed"
          });
          return;
        }
        if (result.status === "ok") {
          marker = classifyPypiVersion(
            row.dataset.installedVersion || "",
            result.version
          );
          setPypiLookupCell(row, {
            markerText: marker,
            toneClass: marker === "Latest" ? "platform-pypi-success" : "platform-pypi-warning",
            versionText: result.version
          });
          return;
        }
        if (result.status === "not_found") {
          setPypiLookupCell(row, {
            markerText: "",
            toneClass: "platform-pypi-danger",
            versionText: result.version
          });
          return;
        }
        setPypiLookupCell(row, {
          markerText: "",
          toneClass: "platform-pypi-danger",
          versionText: result.version
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
            taskFactories[taskIndex]().then((result) => {
              results[taskIndex] = result;
            }).catch((error) => {
              results[taskIndex] = {
                error
              };
            }).finally(() => {
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
          "#platform-packages-body tr[data-package-name]"
        )
      );
      var packageLookupMap = /* @__PURE__ */ new Map();
      var packageNames;
      var taskFactories;
      if (!rows.length) {
        return Promise.resolve();
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
          versionText: "Loading\u2026"
        });
      });
      setPlatformPypiButtonState({
        isLoading: true,
        label: "Fetching PyPI Versions\u2026"
      });
      taskFactories = packageNames.map((packageLookupName) => {
        return function taskFactory() {
          return fetchLatestPyPiVersion(packageLookupName).then((result) => {
            packageLookupMap.set(packageLookupName, result);
            applyPypiLookupResult(packageLookupName, result);
            return result;
          }).catch(() => {
            var failureResult = {
              marker: "",
              status: "failed",
              version: "Lookup failed"
            };
            packageLookupMap.set(packageLookupName, failureResult);
            applyPypiLookupResult(packageLookupName, failureResult);
            return failureResult;
          });
        };
      });
      return runWithConcurrency(taskFactories, PYPI_LOOKUP_CONCURRENCY).finally(
        () => {
          setPlatformPypiButtonState({
            isLoading: false
          });
        }
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
      var lifecycleStatus = metadata && metadata.api_lifecycle && typeof metadata.api_lifecycle.status === "string" ? metadata.api_lifecycle.status : "";
      tbody.innerHTML = "";
      tbody.appendChild(
        createPlatformRow("API Version", metadata.api_version || "")
      );
      tbody.appendChild(createPlatformRow("Lifecycle Status", lifecycleStatus));
      tbody.appendChild(
        createPlatformRow("Generated At", metadata.generated_at || "")
      );
      tbody.appendChild(
        createPlatformRow("Package Version", metadata.package_version || "")
      );
    }
    function renderPlatformSnapshot(data) {
      var platformData = data.platform || {};
      var runtime = platformData.runtime || {};
      var dependencyData = platformData.python_dependencies || {};
      var source = dependencyData.source || {};
      var packages = Array.isArray(dependencyData.packages) ? dependencyData.packages : [];
      var warnings = Array.isArray(platformData.warnings) ? platformData.warnings : [];
      var metadata = data.metadata || {};
      updatePlatformSummary(packages, warnings);
      renderPlatformRuntime(runtime);
      renderPlatformSource(source);
      renderPlatformWarnings(warnings);
      renderPlatformPackages(packages);
      renderPlatformMetadata(metadata);
      bindPlatformPyPiLookup();
      setPlatformPypiButtonState({
        isLoading: false
      });
    }
    function validateResponsePayload(data, reportKind) {
      if (reportKind === "platform") {
        if (!data || typeof data !== "object" || typeof data.platform !== "object" || typeof data.metadata !== "object") {
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
        headers: buildReportRequestHeaders(reportAccessToken)
      }).then(
        (response) => response.json().catch(() => {
          throw new Error("Report data response was not valid JSON.");
        }).then((data) => {
          if (!response.ok) {
            throw new Error(
              data && data.error ? data.error : "Report data request failed (" + response.status + ")."
            );
          }
          return validateResponsePayload(data, reportKind);
        })
      ).then((data) => {
        if (reportKind === "platform") {
          renderPlatformSnapshot(data);
          return data;
        }
        var urls = Array.isArray(data.urls) ? data.urls : [];
        updateSummary(data.metadata || null, data.count || urls.length);
        renderRows(urls, reportKind);
        return data;
      }).catch((error) => {
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
      bindPlatformPyPiLookup,
      loadReportData,
      lookupPlatformPyPiVersions
    };
  })();

  // assets_src/js/report_bootstrap.js
  (() => {
    function initReport() {
      var report = window.UnveilReport;
      var retryButton;
      if (!report || document.body.dataset.unveilReportInitialized === "true") {
        return;
      }
      document.body.dataset.unveilReportInitialized = "true";
      report.helpers.showLoadingScreen("Loading report data...", {
        delayMs: 200
      });
      retryButton = document.getElementById("report-retry-button");
      if (retryButton && retryButton.dataset.unveilRetryBound !== "true") {
        retryButton.dataset.unveilRetryBound = "true";
        retryButton.addEventListener("click", () => {
          window.location.reload();
        });
      }
      report.components.defineCustomElements();
      report.data.loadReportData().then(() => {
        report.sorting.init();
        report.filters.init();
        report.helpers.setPageState("ready");
      }).catch((error) => {
        report.helpers.showErrorScreen(
          error.message || "Unable to load report data."
        );
      });
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initReport);
    } else {
      initReport();
    }
  })();
})();
