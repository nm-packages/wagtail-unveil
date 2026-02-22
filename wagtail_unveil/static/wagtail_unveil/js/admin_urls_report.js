document.querySelectorAll(".filter-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
        document.querySelectorAll(".filter-btn").forEach(function(b) { b.classList.remove("active"); });
        btn.classList.add("active");
        var filter = btn.getAttribute("data-filter");
        document.querySelectorAll("tbody tr").forEach(function(row) {
            var hasParams = row.getAttribute("data-has-parameters") === "true";
            if (filter === "all") {
                row.classList.remove("hidden");
            } else if (filter === "static") {
                row.classList.toggle("hidden", hasParams);
            } else {
                row.classList.toggle("hidden", !hasParams);
            }
        });
    });
});

var testState = null;

function pauseTests() {
    if (!testState) return;
    testState.paused = true;
    var pauseBtn = document.querySelector(".pause-btn");
    var cancelBtn = document.querySelector(".cancel-btn");
    pauseBtn.textContent = "Continue";
    pauseBtn.onclick = continueTests;
    cancelBtn.classList.remove("hidden");
    testState.summaryEl.innerHTML = "Paused: " + testState.done + "/" + testState.total;
}

function continueTests() {
    if (!testState) return;
    testState.paused = false;
    var pauseBtn = document.querySelector(".pause-btn");
    var cancelBtn = document.querySelector(".cancel-btn");
    pauseBtn.textContent = "Pause";
    pauseBtn.onclick = pauseTests;
    cancelBtn.classList.add("hidden");
    testState.runNext(testState.nextIndex);
}

function cancelTests() {
    if (!testState) return;
    testState.cancelled = true;
    testState.paused = false;
    finishTests();
}

function finishTests() {
    var s = testState;
    var testAllBtn = document.querySelector(".test-all-btn");
    var pauseBtn = document.querySelector(".pause-btn");
    var cancelBtn = document.querySelector(".cancel-btn");
    testAllBtn.classList.remove("hidden");
    pauseBtn.classList.add("hidden");
    cancelBtn.classList.add("hidden");
    var suffix = s.cancelled ? " (cancelled)" : "";
    s.summaryEl.innerHTML = "Results: <span class='pass'>" + s.passed + " passed</span>, <span class='fail'>" + s.failed + " failed</span> out of " + s.done + "/" + s.total + suffix;
    testState = null;
}

function testAll() {
    var testAllBtn = document.querySelector(".test-all-btn");
    var pauseBtn = document.querySelector(".pause-btn");
    var cancelBtn = document.querySelector(".cancel-btn");
    var summaryEl = document.getElementById("test-all-summary");
    var buttons = Array.from(document.querySelectorAll(".test-btn:not(:disabled)"));
    if (buttons.length === 0) return;

    testAllBtn.classList.add("hidden");
    pauseBtn.classList.remove("hidden");
    pauseBtn.textContent = "Pause";
    pauseBtn.onclick = pauseTests;
    cancelBtn.classList.add("hidden");
    summaryEl.classList.remove("hidden");

    testState = {
        total: buttons.length,
        done: 0,
        passed: 0,
        failed: 0,
        paused: false,
        cancelled: false,
        nextIndex: 0,
        summaryEl: summaryEl,
        buttons: buttons,
        runNext: null,
    };

    // Clear all status cells in visible rows before testing
    document.querySelectorAll("tbody tr:not(.hidden) .status-cell").forEach(function(cell) {
        cell.innerHTML = "\u2014";
    });

    function updateSummary() {
        var s = testState;
        if (s.done < s.total) {
            pauseBtn.textContent = "Pause (" + s.done + "/" + s.total + ")";
            s.summaryEl.innerHTML = "Progress: " + s.done + "/" + s.total;
        } else {
            finishTests();
        }
    }

    function runNext(i) {
        var s = testState;
        if (!s || s.cancelled) { if (s) finishTests(); return; }
        if (s.paused) { s.nextIndex = i; return; }
        if (i >= s.buttons.length) return;
        s.nextIndex = i;
        var btn = s.buttons[i];
        var row = btn.closest("tr");
        var url = btn.getAttribute("onclick").match(/'([^']+)'/)[1];
        btn.disabled = true;
        btn.textContent = "\u2026";
        var statusCell = btn.parentElement.nextElementSibling;
        fetch(url, { credentials: "include" }).then(function(response) {
            var code = response.status;
            var cls = "status-err";
            if (code >= 200 && code < 300) { cls = "status-2xx"; s.passed++; }
            else if (code >= 300 && code < 400) { cls = "status-3xx"; s.failed++; }
            else if (code >= 400 && code < 500) { cls = "status-4xx"; s.failed++; }
            else if (code >= 500) { cls = "status-5xx"; s.failed++; }
            statusCell.innerHTML = "<span class='status " + cls + "'>" + code + "</span>";
            btn.disabled = false;
            btn.textContent = "Test";
            s.done++;
            updateSummary();
            // Move failed rows to top of table
            if (cls !== "status-2xx") {
                row.closest("tbody").prepend(row);
            }
            setTimeout(function() { runNext(i + 1); }, 100);
        }).catch(function() {
            statusCell.innerHTML = "<span class='status status-err'>ERR</span>";
            btn.disabled = false;
            btn.textContent = "Test";
            s.failed++;
            s.done++;
            updateSummary();
            // Move failed rows to top of table
            row.closest("tbody").prepend(row);
            setTimeout(function() { runNext(i + 1); }, 100);
        });
    }

    testState.runNext = runNext;
    updateSummary();
    runNext(0);
}

function testUrl(btn, url) {
    btn.disabled = true;
    btn.textContent = "\u2026";
    var row = btn.closest("tr");
    var statusCell = btn.parentElement.nextElementSibling;
    // Clear previous result before fetching
    statusCell.innerHTML = "\u2014";
    fetch(url, { credentials: "include" }).then(function(response) {
        var code = response.status;
        var cls = "status-err";
        if (code >= 200 && code < 300) cls = "status-2xx";
        else if (code >= 300 && code < 400) cls = "status-3xx";
        else if (code >= 400 && code < 500) cls = "status-4xx";
        else if (code >= 500) cls = "status-5xx";
        statusCell.innerHTML = "<span class='status " + cls + "'>" + code + "</span>";
        btn.disabled = false;
        btn.textContent = "Test";
        // Move failed rows to top of table
        if (cls !== "status-2xx") {
            row.closest("tbody").prepend(row);
        }
    }).catch(function() {
        statusCell.innerHTML = "<span class='status status-err'>ERR</span>";
        btn.disabled = false;
        btn.textContent = "Test";
        // Move failed rows to top of table
        row.closest("tbody").prepend(row);
    });
}
