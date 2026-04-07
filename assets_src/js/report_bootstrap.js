(() => {
  function initReport() {
    var report = window.UnveilReport;
    var retryButton;

    if (!report || document.body.dataset.unveilReportInitialized === "true") {
      return;
    }

    document.body.dataset.unveilReportInitialized = "true";
    report.helpers.showLoadingScreen("Loading report data...", {
      delayMs: 200,
    });
    retryButton = document.getElementById("report-retry-button");
    if (retryButton && retryButton.dataset.unveilRetryBound !== "true") {
      retryButton.dataset.unveilRetryBound = "true";
      retryButton.addEventListener("click", () => {
        window.location.reload();
      });
    }
    report.components.defineCustomElements();
    report.data
      .loadReportData()
      .then(() => {
        report.sorting.init();
        report.filters.init();
        report.helpers.setPageState("ready");
      })
      .catch((error) => {
        report.helpers.showErrorScreen(
          error.message || "Unable to load report data.",
        );
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initReport);
  } else {
    initReport();
  }
})();
