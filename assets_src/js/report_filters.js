(function() {
    "use strict";

    var report = window.UnveilReport;
    var state = report.state;
    var helpers = report.helpers;

    function getSearchableColumns() {
        return document.querySelectorAll("th[data-sort-col]");
    }

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

        sortableCols = getSearchableColumns();
        for (index = 0; index < sortableCols.length; index++) {
            colIdx = parseInt(sortableCols[index].getAttribute("data-sort-col"), 10);
            text = row.children[colIdx].textContent.toLowerCase();
            if (text.indexOf(searchTerm) !== -1) {
                return true;
            }
        }

        return false;
    }

    function rowMatchesUntestableFilter(row) {
        if (!helpers.isDataRow(row)) {
            return true;
        }

        if (!state.hideUntestable) {
            return true;
        }

        return !row.classList.contains("untestable");
    }

    function applyFilters() {
        document.querySelectorAll("tbody tr").forEach(function(row) {
            var visible = rowMatchesSearch(row) && rowMatchesUntestableFilter(row);
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
        applyFilters: applyFilters,
        init: init,
        syncUntestableButton: syncUntestableButton,
        toggleUntestable: toggleUntestable,
        updateSearchTerm: updateSearchTerm,
    };
})();
