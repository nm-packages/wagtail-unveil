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

function testAll() {
    var testAllBtn = document.querySelector(".test-all-btn");
    var summaryEl = document.getElementById("test-all-summary");
    var buttons = Array.from(document.querySelectorAll(".test-btn:not(:disabled)"));
    if (buttons.length === 0) return;

    testAllBtn.disabled = true;
    summaryEl.classList.remove("hidden");
    var total = buttons.length;
    var done = 0;
    var passed = 0;
    var failed = 0;

    // Clear all status cells in visible rows before testing
    document.querySelectorAll("tbody tr:not(.hidden) .status-cell").forEach(function(cell) {
        cell.innerHTML = "\u2014";
    });

    function updateSummary() {
        if (done < total) {
            testAllBtn.textContent = "Testing " + done + "/" + total + "\u2026";
            summaryEl.innerHTML = "Progress: " + done + "/" + total;
        } else {
            testAllBtn.textContent = "Test All";
            testAllBtn.disabled = false;
            summaryEl.innerHTML = "Results: <span class='pass'>" + passed + " passed</span>, <span class='fail'>" + failed + " failed</span> out of " + total;
        }
    }

    function runNext(i) {
        if (i >= buttons.length) return;
        var btn = buttons[i];
        var row = btn.closest("tr");
        var url = btn.getAttribute("onclick").match(/'([^']+)'/)[1];
        btn.disabled = true;
        btn.textContent = "\u2026";
        var statusCell = btn.parentElement.nextElementSibling;
        fetch(url, { credentials: "include" }).then(function(response) {
            var code = response.status;
            var cls = "status-err";
            if (code >= 200 && code < 300) { cls = "status-2xx"; passed++; }
            else if (code >= 300 && code < 400) { cls = "status-3xx"; failed++; }
            else if (code >= 400 && code < 500) { cls = "status-4xx"; failed++; }
            else if (code >= 500) { cls = "status-5xx"; failed++; }
            statusCell.innerHTML = "<span class='status " + cls + "'>" + code + "</span>";
            btn.disabled = false;
            btn.textContent = "Test";
            done++;
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
            failed++;
            done++;
            updateSummary();
            // Move failed rows to top of table
            row.closest("tbody").prepend(row);
            setTimeout(function() { runNext(i + 1); }, 100);
        });
    }

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
