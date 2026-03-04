(function() {
    "use strict";

    function bindRetryButton() {
        var button = document.getElementById("report-retry-button");

        if (!button || button.dataset.unveilRetryBound === "true") {
            return;
        }

        button.dataset.unveilRetryBound = "true";
        button.addEventListener("click", function() {
            window.location.reload();
        });
    }

    function initReport() {
        var report = window.UnveilReport;

        if (!report || document.body.dataset.unveilReportInitialized === "true") {
            return;
        }

        document.body.dataset.unveilReportInitialized = "true";
        report.helpers.showLoadingScreen("Loading report data...");
        bindRetryButton();
        report.components.defineCustomElements();
        report.data.loadReportData().then(function() {
            report.sorting.init();
            report.filters.init();
            report.helpers.setPageState("ready");
        }).catch(function(error) {
            report.helpers.showErrorScreen(error.message || "Unable to load report data.");
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initReport);
    } else {
        initReport();
    }
})();
