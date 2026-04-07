(() => {
  var report = window.UnveilReport;

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
      button.addEventListener("click", () => {
        window.location.reload();
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

      input.addEventListener("input", () => {
        clear.classList.toggle("hidden", !input.value);
        report.filters.updateSearchTerm(input.value);
      });

      clear.addEventListener("click", () => {
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
        button.addEventListener("click", () => {
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
    [
      ["unveil-reset-button", UnveilResetButton],
      ["unveil-toggle-untestable-button", UnveilToggleUntestableButton],
      ["unveil-test-all-button", UnveilTestAllButton],
      ["unveil-pause-button", UnveilPauseButton],
      ["unveil-cancel-button", UnveilCancelButton],
      ["unveil-search-input", UnveilSearchInput],
      ["unveil-test-button", UnveilTestButton],
      ["unveil-open-button", UnveilOpenButton],
    ].forEach(([name, constructor]) => {
      if (!customElements.get(name)) {
        customElements.define(name, constructor);
      }
    });
  }

  report.components = {
    defineCustomElements: defineCustomElements,
  };
})();
