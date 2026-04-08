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
      state.currentSortAsc ? "asc" : "desc",
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
    init: init,
  };
})();
