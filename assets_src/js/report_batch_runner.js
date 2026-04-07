(() => {
  var report = window.UnveilReport;
  var helpers = report.helpers;
  var state = report.state;
  var RUN_STATUS_FINISHED = "finished";
  var RUN_STATUS_RUNNING = "running";
  var RUN_STATUS_PAUSED = "paused";
  var RUN_STATUS_STOPPED = "stopped";

  function getControls() {
    return {
      cancelButton: document.querySelector(".cancel-btn"),
      pauseButton: document.querySelector(".pause-btn"),
      summary: document.getElementById("test-all-summary"),
      testAllButton: document.querySelector(".test-all-btn"),
    };
  }

  function syncControlsForIdle() {
    var controls = getControls();

    controls.testAllButton.classList.remove("hidden");
    controls.pauseButton.classList.add("hidden");
    controls.cancelButton.classList.add("hidden");
  }

  function syncControlsForRunning() {
    var controls = getControls();

    controls.testAllButton.classList.add("hidden");
    controls.pauseButton.classList.remove("hidden");
    controls.cancelButton.classList.add("hidden");
    controls.summary.classList.remove("hidden");
  }

  function finishTests() {
    var controls = getControls();
    var runState = state.testState;
    var tbody;
    var banner;
    var bannerCell;

    if (!runState) {
      return;
    }

    runState.status = RUN_STATUS_FINISHED;

    syncControlsForIdle();

    runState.summaryEl.innerHTML =
      'Results: <span class="pass">' +
      runState.passed +
      " passed</span>, " +
      '<span class="fail">' +
      runState.failed +
      " failed</span> out of " +
      runState.done +
      "/" +
      runState.total;

    state.testState = null;

    if (runState.failed === 0 && runState.total > 0) {
      tbody = helpers.getTableBody();
      banner = document.createElement("tr");
      banner.className = "success-banner-row";
      bannerCell = document.createElement("td");
      bannerCell.setAttribute("colspan", "100");
      bannerCell.innerHTML =
        "&#10003; All " +
        runState.total +
        " URLs returned 2xx \u2014 no errors found.";
      banner.appendChild(bannerCell);
      tbody.prepend(banner);
    }

    controls.pauseButton.textContent = "Pause";
  }

  function updateSummary() {
    var controls = getControls();
    var runState = state.testState;

    if (!runState) {
      return;
    }

    if (runState.status === RUN_STATUS_PAUSED) {
      controls.pauseButton.textContent = "Continue";
      runState.summaryEl.innerHTML =
        "Paused: " + runState.done + "/" + runState.total;
      return;
    }

    if (runState.done < runState.total) {
      controls.pauseButton.textContent =
        "Pause (" + runState.done + "/" + runState.total + ")";
      runState.summaryEl.innerHTML =
        "Progress: " + runState.done + "/" + runState.total;
      return;
    }

    finishTests();
  }

  function runNext(index) {
    var runState = state.testState;

    if (!runState) {
      return;
    }

    if (runState.status === RUN_STATUS_PAUSED) {
      runState.nextIndex = index;
      return;
    }

    if (runState.status === RUN_STATUS_STOPPED) {
      return;
    }

    if (index >= runState.buttons.length) {
      finishTests();
      return;
    }

    runState.nextIndex = index;

    report.rowActions.testUrlButton(runState.buttons[index], {
      onComplete: (result) => {
        if (result.statusClass === "status-2xx") {
          runState.passed += 1;
        } else {
          runState.failed += 1;
        }

        runState.done += 1;
        updateSummary();

        if (state.testState) {
          window.setTimeout(() => {
            runNext(index + 1);
          }, 100);
        }
      },
    });
  }

  function pauseTests() {
    var controls = getControls();
    var runState = state.testState;

    if (!runState) {
      return;
    }

    if (runState.status !== RUN_STATUS_RUNNING) {
      return;
    }

    runState.status = RUN_STATUS_PAUSED;
    controls.pauseButton.textContent = "Continue";
    controls.cancelButton.classList.remove("hidden");
    runState.summaryEl.innerHTML =
      "Paused: " + runState.done + "/" + runState.total;
  }

  function continueTests() {
    var controls = getControls();
    var runState = state.testState;

    if (!runState) {
      return;
    }

    if (runState.status !== RUN_STATUS_PAUSED) {
      return;
    }

    runState.status = RUN_STATUS_RUNNING;
    controls.pauseButton.textContent = "Pause";
    controls.cancelButton.classList.add("hidden");
    runNext(runState.nextIndex);
  }

  function handlePauseClick() {
    var runState = state.testState;

    if (!runState) {
      return;
    }

    if (runState.status === RUN_STATUS_PAUSED) {
      continueTests();
      return;
    }

    if (runState.status === RUN_STATUS_RUNNING) {
      pauseTests();
    }
  }

  function cancelTests() {
    if (state.testState) {
      state.testState.status = RUN_STATUS_STOPPED;
    }
    window.location.reload();
  }

  function resetVisibleStatuses() {
    document
      .querySelectorAll("tbody tr:not(.hidden):not(.untestable) .status-cell")
      .forEach((cell) => {
        cell.innerHTML = "\u2014";
      });
  }

  function testAll() {
    var controls = getControls();
    var buttons = helpers.getVisibleTestButtons();

    if (buttons.length === 0) {
      return;
    }

    syncControlsForRunning();
    controls.pauseButton.textContent = "Pause";
    helpers.clearSuccessBanner();
    resetVisibleStatuses();

    state.testState = {
      buttons: buttons,
      done: 0,
      failed: 0,
      nextIndex: 0,
      passed: 0,
      summaryEl: controls.summary,
      status: RUN_STATUS_RUNNING,
      total: buttons.length,
    };

    updateSummary();
    runNext(0);
  }

  report.batchRunner = {
    cancelTests: cancelTests,
    continueTests: continueTests,
    handlePauseClick: handlePauseClick,
    pauseTests: pauseTests,
    testAll: testAll,
  };
})();
