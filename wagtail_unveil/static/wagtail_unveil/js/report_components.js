(function() {
    "use strict";

    var report = window.UnveilReport;

    function defineCustomElement(name, constructor) {
        if (!customElements.get(name)) {
            customElements.define(name, constructor);
        }
    }

    class UnveilResetButton extends HTMLElement {
        connectedCallback() {
            var button;

            if (this.querySelector("button")) {
                return;
            }

            button = document.createElement("button");
            button.type = "button";
            button.className = "reset-btn";
            button.textContent = "Reset";
            button.addEventListener("click", function() {
                window.location.reload();
            });
            this.appendChild(button);
        }
    }

    class UnveilHelpButton extends HTMLElement {
        connectedCallback() {
            var button;

            if (this.querySelector("button")) {
                return;
            }

            button = document.createElement("button");
            button.type = "button";
            button.className = "help-btn";
            button.textContent = "Help";
            button.addEventListener("click", function() {
                button.classList.toggle("active");
                document.querySelector(".help-panel").classList.toggle("hidden");
            });
            this.appendChild(button);
        }
    }

    class UnveilToggleUntestableButton extends HTMLElement {
        connectedCallback() {
            var button;

            if (this.querySelector("button")) {
                return;
            }

            button = document.createElement("button");
            button.type = "button";
            button.className = "toggle-untestable-btn";
            button.addEventListener("click", report.filters.toggleUntestable);
            this.appendChild(button);
        }
    }

    class UnveilTestAllButton extends HTMLElement {
        connectedCallback() {
            var button;

            if (this.querySelector("button")) {
                return;
            }

            button = document.createElement("button");
            button.type = "button";
            button.className = "test-all-btn";
            button.textContent = "Test All";
            button.addEventListener("click", report.batchRunner.testAll);
            this.appendChild(button);
        }
    }

    class UnveilPauseButton extends HTMLElement {
        connectedCallback() {
            var button;

            if (this.querySelector("button")) {
                return;
            }

            button = document.createElement("button");
            button.type = "button";
            button.className = "pause-btn hidden";
            button.textContent = "Pause";
            button.addEventListener("click", report.batchRunner.handlePauseClick);
            this.appendChild(button);
        }
    }

    class UnveilCancelButton extends HTMLElement {
        connectedCallback() {
            var button;

            if (this.querySelector("button")) {
                return;
            }

            button = document.createElement("button");
            button.type = "button";
            button.className = "cancel-btn hidden";
            button.textContent = "Cancel";
            button.addEventListener("click", report.batchRunner.cancelTests);
            this.appendChild(button);
        }
    }

    class UnveilSearchInput extends HTMLElement {
        connectedCallback() {
            var wrapper;
            var input;
            var clear;

            if (this.querySelector("input")) {
                return;
            }

            wrapper = document.createElement("div");
            wrapper.className = "search-wrapper";

            input = document.createElement("input");
            input.type = "text";
            input.className = "search-input";
            input.placeholder = this.getAttribute("placeholder") || "";

            clear = document.createElement("button");
            clear.type = "button";
            clear.className = "search-clear hidden";
            clear.setAttribute("aria-label", "Clear search");
            clear.textContent = "\u00d7";

            input.addEventListener("input", function() {
                clear.classList.toggle("hidden", !input.value);
                report.filters.updateSearchTerm(input.value);
            });

            clear.addEventListener("click", function() {
                input.value = "";
                clear.classList.add("hidden");
                report.filters.updateSearchTerm("");
            });

            wrapper.appendChild(input);
            wrapper.appendChild(clear);
            this.appendChild(wrapper);
        }
    }

    class UnveilTestButton extends HTMLElement {
        connectedCallback() {
            var button;
            var title;
            var url;

            if (this.querySelector("button")) {
                return;
            }

            button = document.createElement("button");
            button.type = "button";
            button.className = "test-btn";
            button.textContent = "Test";

            url = this.dataset.url;
            if (url) {
                button.dataset.url = url;
                button.addEventListener("click", function() {
                    report.rowActions.testUrlButton(button);
                });
            } else {
                button.disabled = true;
            }

            if (this.hasAttribute("disabled")) {
                button.disabled = true;
            }

            title = this.getAttribute("title");
            if (title) {
                button.title = title;
            }

            this.appendChild(button);
        }
    }

    class UnveilOpenButton extends HTMLElement {
        connectedCallback() {
            var link;
            var href;

            if (this.querySelector("a")) {
                return;
            }

            link = document.createElement("a");
            link.className = "open-btn";
            link.textContent = "Open";
            link.target = "_blank";
            link.rel = "noopener noreferrer";

            href = this.getAttribute("href");
            if (href) {
                link.href = href;
            }

            this.appendChild(link);
        }
    }

    function defineCustomElements() {
        defineCustomElement("unveil-reset-button", UnveilResetButton);
        defineCustomElement("unveil-help-button", UnveilHelpButton);
        defineCustomElement("unveil-toggle-untestable-button", UnveilToggleUntestableButton);
        defineCustomElement("unveil-test-all-button", UnveilTestAllButton);
        defineCustomElement("unveil-pause-button", UnveilPauseButton);
        defineCustomElement("unveil-cancel-button", UnveilCancelButton);
        defineCustomElement("unveil-search-input", UnveilSearchInput);
        defineCustomElement("unveil-test-button", UnveilTestButton);
        defineCustomElement("unveil-open-button", UnveilOpenButton);
    }

    report.components = {
        defineCustomElements: defineCustomElements,
    };
})();
