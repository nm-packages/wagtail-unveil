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
        10,
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

      if (
        visible &&
        helpers.isDataRow(row) &&
        state.hideUntestable &&
        row.classList.contains("untestable")
      ) {
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

    button.textContent = state.hideUntestable
      ? "Show Untestable"
      : "Hide Untestable";
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
