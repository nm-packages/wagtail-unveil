(function() {
    "use strict";

    if (window.UnveilReport) {
        return;
    }

    function getCookieFlag(name) {
        var match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
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
            window.UnveilReport.state.loadingFeedbackTimer = window.setTimeout(function() {
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
            document.querySelectorAll("tbody tr:not(.hidden) .test-btn:not(:disabled)")
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
        statusCell.innerHTML = "<span class=\"status " + statusClass + "\">" + label + "</span>";
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
            testState: null,
        },
        helpers: {
            classifyStatus: classifyStatus,
            clearLoadingFeedbackTimer: clearLoadingFeedbackTimer,
            clearSuccessBanner: clearSuccessBanner,
            getTableBody: getTableBody,
            getVisibleTestButtons: getVisibleTestButtons,
            isDataRow: isDataRow,
            moveFailedRowToTop: moveFailedRowToTop,
            renderStatus: renderStatus,
            setLoadingFeedbackVisibility: setLoadingFeedbackVisibility,
            setPageState: setPageState,
            setCookieFlag: setCookieFlag,
            showErrorScreen: showErrorScreen,
            showLoadingScreen: showLoadingScreen,
        },
    };
})();
