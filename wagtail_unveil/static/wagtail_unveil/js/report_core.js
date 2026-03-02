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

    function clearSuccessBanner() {
        var banner = document.querySelector("tbody .success-banner-row");
        if (banner) {
            banner.remove();
        }
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
            testState: null,
        },
        helpers: {
            classifyStatus: classifyStatus,
            clearSuccessBanner: clearSuccessBanner,
            getTableBody: getTableBody,
            getVisibleTestButtons: getVisibleTestButtons,
            moveFailedRowToTop: moveFailedRowToTop,
            renderStatus: renderStatus,
            setCookieFlag: setCookieFlag,
        },
    };
})();
