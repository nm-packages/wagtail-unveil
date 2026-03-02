(function() {
    "use strict";

    function initReport() {
        var report = window.UnveilReport;

        if (!report || document.body.dataset.unveilReportInitialized === "true") {
            return;
        }

        document.body.dataset.unveilReportInitialized = "true";
        report.components.defineCustomElements();
        report.sorting.init();
        report.filters.init();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initReport);
    } else {
        initReport();
    }
})();
