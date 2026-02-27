var currentSearchTerm = "";
var currentSortCol = null;
var currentSortAsc = true;
var hideUntestable = (function() {
    var match = document.cookie.match(/(?:^|; )unveil_hide_untestable=([^;]*)/);
    return match ? match[1] === "1" : false;
})();

function applyFilters() {
    var rows = document.querySelectorAll("tbody tr");
    rows.forEach(function(row) {
        var searchMatch = !currentSearchTerm;
        if (!searchMatch) {
            var sortableCols = document.querySelectorAll("th[data-sort-col]");
            for (var i = 0; i < sortableCols.length; i++) {
                var colIdx = parseInt(sortableCols[i].getAttribute("data-sort-col"));
                var text = row.children[colIdx].textContent.toLowerCase();
                if (text.indexOf(currentSearchTerm) !== -1) {
                    searchMatch = true;
                    break;
                }
            }
        }
        var untestableMatch = true;
        if (hideUntestable) {
            if (row.classList.contains("untestable")) {
                untestableMatch = false;
            }
        }
        row.classList.toggle("hidden", !searchMatch || !untestableMatch);
    });
}

function toggleUntestable() {
    hideUntestable = !hideUntestable;
    var btn = document.querySelector(".toggle-untestable-btn");
    btn.textContent = hideUntestable ? "Show Untestable" : "Hide Untestable";
    btn.classList.toggle("active", hideUntestable);
    document.cookie = "unveil_hide_untestable=" + (hideUntestable ? "1" : "0") + "; path=/; max-age=31536000";
    applyFilters();
}

var searchInput = document.querySelector(".search-input");
var searchClear = document.querySelector(".search-clear");

searchInput.addEventListener("input", function() {
    currentSearchTerm = this.value.toLowerCase();
    searchClear.classList.toggle("hidden", !this.value);
    applyFilters();
});

searchClear.addEventListener("click", function() {
    searchInput.value = "";
    currentSearchTerm = "";
    searchClear.classList.add("hidden");
    applyFilters();
});


// Column sorting
document.querySelectorAll("th[data-sort-col]").forEach(function(th) {
    th.addEventListener("click", function() {
        var col = parseInt(th.getAttribute("data-sort-col"));
        if (currentSortCol === col) {
            currentSortAsc = !currentSortAsc;
        } else {
            currentSortCol = col;
            currentSortAsc = true;
        }
        // Update sort indicators
        document.querySelectorAll("th[data-sort-col]").forEach(function(h) {
            h.removeAttribute("data-sort-dir");
        });
        th.setAttribute("data-sort-dir", currentSortAsc ? "asc" : "desc");
        // Sort rows
        var tbody = document.querySelector("tbody");
        var rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort(function(a, b) {
            var aText = a.children[col].textContent.toLowerCase();
            var bText = b.children[col].textContent.toLowerCase();
            if (aText < bText) return currentSortAsc ? -1 : 1;
            if (aText > bText) return currentSortAsc ? 1 : -1;
            return 0;
        });
        rows.forEach(function(row) { tbody.appendChild(row); });
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
    location.reload();
}

function finishTests() {
    var s = testState;
    var passed = s.passed;
    var failed = s.failed;
    var total = s.total;
    var cancelled = s.cancelled;
    var testAllBtn = document.querySelector(".test-all-btn");
    var pauseBtn = document.querySelector(".pause-btn");
    var cancelBtn = document.querySelector(".cancel-btn");
    testAllBtn.classList.remove("hidden");
    pauseBtn.classList.add("hidden");
    cancelBtn.classList.add("hidden");
    var suffix = cancelled ? " (cancelled)" : "";
    s.summaryEl.innerHTML = "Results: <span class='pass'>" + passed + " passed</span>, <span class='fail'>" + failed + " failed</span> out of " + s.done + "/" + total + suffix;
    testState = null;
    if (!cancelled && failed === 0 && total > 0) {
        var tbody = document.querySelector("tbody");
        var banner = document.createElement("tr");
        banner.className = "success-banner-row";
        var td = document.createElement("td");
        td.setAttribute("colspan", "100");
        td.innerHTML = "&#10003; All " + total + " URLs returned 2xx \u2014 no errors found.";
        banner.appendChild(td);
        tbody.prepend(banner);
    }
}

function testAll() {
    var testAllBtn = document.querySelector(".test-all-btn");
    var pauseBtn = document.querySelector(".pause-btn");
    var cancelBtn = document.querySelector(".cancel-btn");
    var summaryEl = document.getElementById("test-all-summary");
    var buttons = Array.from(document.querySelectorAll("tbody tr:not(.hidden) .test-btn:not(:disabled)"));
    if (buttons.length === 0) return;

    testAllBtn.classList.add("hidden");
    pauseBtn.classList.remove("hidden");
    pauseBtn.textContent = "Pause";
    pauseBtn.onclick = pauseTests;
    cancelBtn.classList.add("hidden");
    summaryEl.classList.remove("hidden");

    // Remove any existing success banner before starting
    var existingBanner = document.querySelector("tbody .success-banner-row");
    if (existingBanner) existingBanner.remove();

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
    document.querySelectorAll("tbody tr:not(.hidden):not(.untestable) .status-cell").forEach(function(cell) {
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
        var statusCell = btn.closest("td").nextElementSibling;
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

class UnveilResetButton extends HTMLElement {
    connectedCallback() {
        var btn = document.createElement('button');
        btn.className = 'reset-btn';
        btn.textContent = 'Reset';
        btn.addEventListener('click', function() { location.reload(); });
        this.appendChild(btn);
    }
}
customElements.define('unveil-reset-button', UnveilResetButton);

class UnveilHelpButton extends HTMLElement {
    connectedCallback() {
        var btn = document.createElement('button');
        btn.className = 'help-btn';
        btn.textContent = 'Help';
        btn.addEventListener('click', function() {
            btn.classList.toggle('active');
            document.querySelector('.help-panel').classList.toggle('hidden');
        });
        this.appendChild(btn);
    }
}
customElements.define('unveil-help-button', UnveilHelpButton);

class UnveilToggleUntestableButton extends HTMLElement {
    connectedCallback() {
        var btn = document.createElement('button');
        btn.className = 'toggle-untestable-btn';
        btn.textContent = hideUntestable ? 'Show Untestable' : 'Hide Untestable';
        if (hideUntestable) {
            btn.classList.add('active');
            applyFilters();
        }
        btn.addEventListener('click', toggleUntestable);
        this.appendChild(btn);
    }
}
customElements.define('unveil-toggle-untestable-button', UnveilToggleUntestableButton);

class UnveilTestAllButton extends HTMLElement {
    connectedCallback() {
        var btn = document.createElement('button');
        btn.className = 'test-all-btn';
        btn.textContent = 'Test All';
        btn.addEventListener('click', testAll);
        this.appendChild(btn);
    }
}
customElements.define('unveil-test-all-button', UnveilTestAllButton);

class UnveilPauseButton extends HTMLElement {
    connectedCallback() {
        var btn = document.createElement('button');
        btn.className = 'pause-btn hidden';
        btn.textContent = 'Pause';
        this.appendChild(btn);
    }
}
customElements.define('unveil-pause-button', UnveilPauseButton);

class UnveilCancelButton extends HTMLElement {
    connectedCallback() {
        var btn = document.createElement('button');
        btn.className = 'cancel-btn hidden';
        btn.textContent = 'Cancel';
        btn.addEventListener('click', cancelTests);
        this.appendChild(btn);
    }
}
customElements.define('unveil-cancel-button', UnveilCancelButton);

function testUrl(btn, url) {
    btn.disabled = true;
    btn.textContent = "\u2026";
    var row = btn.closest("tr");
    var statusCell = btn.closest("td").nextElementSibling;
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
