(function() {
    "use strict";

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

    function getFeedbackElements() {
        return {
            error: document.getElementById("report-error"),
            loading: document.getElementById("report-loading"),
        };
    }

    function setText(element, value) {
        if (element) {
            element.textContent = value;
        }
    }

    function showLoading(message) {
        var feedback = getFeedbackElements();

        setText(feedback.loading, message);
        feedback.loading.classList.remove("hidden");
        feedback.error.classList.add("hidden");
        feedback.error.textContent = "";
    }

    function hideLoading() {
        getFeedbackElements().loading.classList.add("hidden");
    }

    function showError(message) {
        var feedback = getFeedbackElements();

        setText(feedback.error, message);
        feedback.error.classList.remove("hidden");
        feedback.loading.classList.add("hidden");
    }

    function updateSummary(metadata, fallbackCount) {
        var summary = getSummaryElements();
        var totalCount = metadata && typeof metadata.total_count === "number" ? metadata.total_count : fallbackCount;
        var testableCount = metadata && typeof metadata.testable_count === "number" ? metadata.testable_count : 0;
        var untestableCount = metadata && typeof metadata.untestable_count === "number" ? metadata.untestable_count : 0;

        setText(summary.total, String(totalCount));
        setText(summary.testable, String(testableCount));
        setText(summary.untestable, String(untestableCount));
    }

    function getRequestUrl(item, reportKind) {
        if (reportKind === "backend") {
            return "/" + (item.resolved_route || item.route);
        }

        return item.url;
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
        var routeLabel = item.route.indexOf("admin/") === 0 ? item.route.slice(6) : item.route;

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

    function renderRows(urls, reportKind) {
        var tbody = report.helpers.getTableBody();

        tbody.innerHTML = "";

        if (!urls.length) {
            showLoading("No URLs found.");
            return;
        }

        urls.forEach(function(item) {
            if (reportKind === "backend") {
                tbody.appendChild(createBackendRow(item));
                return;
            }

            tbody.appendChild(createFrontendRow(item));
        });

        hideLoading();
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
            showError("Report configuration is missing.");
            return Promise.resolve();
        }

        showLoading("Loading report data...");

        return fetch(config.apiUrl, {
            credentials: "include",
            headers: {
                Accept: "application/json",
            },
        }).then(function(response) {
            return response.json().catch(function() {
                return null;
            }).then(function(data) {
                if (!response.ok) {
                    throw new Error(extractErrorMessage(response, data));
                }

                return data;
            });
        }).then(function(data) {
            var urls = Array.isArray(data.urls) ? data.urls : [];

            updateSummary(data.metadata || null, data.count || urls.length);
            renderRows(urls, config.reportKind);
        }).catch(function(error) {
            showError(error.message || "Unable to load report data.");
            updateSummary(null, 0);
            report.helpers.getTableBody().innerHTML = "";
        });
    }

    report.data = {
        loadReportData: loadReportData,
    };
})();
