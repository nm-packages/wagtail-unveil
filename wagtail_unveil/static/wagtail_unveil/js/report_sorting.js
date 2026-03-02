(function() {
    "use strict";

    var report = window.UnveilReport;
    var state = report.state;

    function sortRowsByColumn(col) {
        var tbody = document.querySelector("tbody");
        var rows = Array.from(tbody.querySelectorAll("tr"));

        rows.sort(function(a, b) {
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

        rows.forEach(function(row) {
            tbody.appendChild(row);
        });
    }

    function updateSortIndicators(activeHeader) {
        document.querySelectorAll("th[data-sort-col]").forEach(function(header) {
            header.removeAttribute("data-sort-dir");
        });

        activeHeader.setAttribute("data-sort-dir", state.currentSortAsc ? "asc" : "desc");
    }

    function handleSortClick(event) {
        var header = event.currentTarget;
        var col = parseInt(header.getAttribute("data-sort-col"), 10);

        if (state.currentSortCol === col) {
            state.currentSortAsc = !state.currentSortAsc;
        } else {
            state.currentSortCol = col;
            state.currentSortAsc = true;
        }

        updateSortIndicators(header);
        sortRowsByColumn(col);
    }

    function init() {
        document.querySelectorAll("th[data-sort-col]").forEach(function(header) {
            if (header.dataset.unveilSortBound === "true") {
                return;
            }

            header.dataset.unveilSortBound = "true";
            header.addEventListener("click", handleSortClick);
        });
    }

    report.sorting = {
        init: init,
    };
})();
