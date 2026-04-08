import { beforeEach, describe, expect, test } from "vitest";

import {
  loadBundleScript,
  resetReportDom,
  stubFetchResponse,
} from "./helpers/reportHarness.js";

async function waitForRender() {
  await Promise.resolve();
  await Promise.resolve();
  await new Promise((resolve) => setTimeout(resolve, 0));
}

describe("report bundle", () => {
  beforeEach(() => {
    resetReportDom({
      apiUrl: "/unveil/api/backend-urls/",
      reportKind: "backend",
    });

    stubFetchResponse({
      count: 1,
      metadata: {
        total_count: 1,
        testable_count: 1,
        untestable_count: 0,
      },
      urls: [
        {
          route: "admin/home/",
          resolved_route: "admin/home/",
          name: "home",
          namespace: "wagtailadmin",
          has_parameters: false,
          view_name: "demo.View",
          page_type: "",
          is_testable: true,
          skip_reason: "",
        },
      ],
    });
  });

  test("boots and renders report rows", async () => {
    loadBundleScript();

    document.dispatchEvent(new Event("DOMContentLoaded"));

    await waitForRender();

    expect(window.UnveilReport).toBeTruthy();
    expect(document.body.dataset.reportState).toBe("ready");
    expect(document.querySelectorAll("tbody tr").length).toBe(1);
    expect(document.querySelector(".test-btn")).toBeTruthy();
  });

  test("reset clears init guard so bootstrap can run again", async () => {
    const firstFetch = stubFetchResponse({
      count: 1,
      metadata: {
        total_count: 1,
        testable_count: 1,
        untestable_count: 0,
      },
      urls: [
        {
          route: "admin/home/",
          resolved_route: "admin/home/",
          name: "home",
          namespace: "wagtailadmin",
          has_parameters: false,
          view_name: "demo.View",
          page_type: "",
          is_testable: true,
          skip_reason: "",
        },
      ],
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(firstFetch).toHaveBeenCalledTimes(1);
    expect(document.body.dataset.unveilReportInitialized).toBe("true");

    resetReportDom({
      apiUrl: "/unveil/api/backend-urls/",
      reportKind: "backend",
    });

    expect(document.body.dataset.unveilReportInitialized).toBeUndefined();

    const secondFetch = stubFetchResponse({
      count: 1,
      metadata: {
        total_count: 1,
        testable_count: 1,
        untestable_count: 0,
      },
      urls: [
        {
          route: "admin/again/",
          resolved_route: "admin/again/",
          name: "again",
          namespace: "wagtailadmin",
          has_parameters: false,
          view_name: "demo.View",
          page_type: "",
          is_testable: true,
          skip_reason: "",
        },
      ],
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(secondFetch).toHaveBeenCalledTimes(1);
    expect(document.body.dataset.reportState).toBe("ready");
    expect(document.querySelectorAll("tbody tr").length).toBe(1);
  });

  test("frontend rows use resolved_url for test and open actions when present", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/frontend-urls/",
      reportKind: "frontend",
    });

    stubFetchResponse({
      count: 1,
      metadata: {
        total_count: 1,
        testable_count: 1,
        untestable_count: 0,
      },
      urls: [
        {
          url: "/events/year/<int:year>/",
          source: "page",
          page_type: "events.EventIndexPage",
          page_title: "Events",
          name: "events_for_year",
          resolved_url: "/events/year/2025/",
          query_params: {},
          is_testable: true,
          skip_reason: "",
        },
      ],
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(document.querySelector(".route").textContent).toBe(
      "/events/year/<int:year>/",
    );
    expect(document.querySelector(".test-btn").dataset.url).toBe(
      "/events/year/2025/",
    );
    expect(document.querySelector(".open-btn").getAttribute("href")).toBe(
      "/events/year/2025/",
    );
  });

  test("backend rows render the page type column", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/backend-urls/",
      reportKind: "backend",
    });

    stubFetchResponse({
      count: 1,
      metadata: {
        total_count: 1,
        testable_count: 1,
        untestable_count: 0,
      },
      urls: [
        {
          route: "admin/pages/<int:page_id>/edit/",
          resolved_route: "admin/pages/3/edit/",
          name: "edit",
          namespace: "wagtailadmin_pages",
          has_parameters: true,
          view_name: "demo.View",
          page_type: "core.StandardPage",
          is_testable: true,
          skip_reason: "",
        },
      ],
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(document.querySelectorAll("tbody td")[3].textContent).toBe(
      "core.StandardPage",
    );
  });

  test("frontend rows append query_params to test and open actions when present", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/frontend-urls/",
      reportKind: "frontend",
    });

    stubFetchResponse({
      count: 1,
      metadata: {
        total_count: 1,
        testable_count: 1,
        untestable_count: 0,
      },
      urls: [
        {
          url: "/api/v2/redirects/find/",
          source: "resolver",
          page_type: "",
          page_title: "",
          name: "find",
          resolved_url: "",
          query_params: {
            html_path: "/sample-old-page-1/",
          },
          is_testable: true,
          skip_reason: "",
        },
      ],
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(document.querySelector(".test-btn").dataset.url).toBe(
      "/api/v2/redirects/find/?html_path=%2Fsample-old-page-1%2F",
    );
    expect(document.querySelector(".open-btn").getAttribute("href")).toBe(
      "/api/v2/redirects/find/?html_path=%2Fsample-old-page-1%2F",
    );
  });

  test("report data loader sends the signed report access header when present", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/backend-urls/",
      reportKind: "backend",
      reportAccessToken: "signed-report-token",
    });

    const fetchMock = stubFetchResponse({
      count: 0,
      metadata: {
        total_count: 0,
        testable_count: 0,
        untestable_count: 0,
      },
      urls: [],
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(fetchMock).toHaveBeenCalledWith(
      "/unveil/api/backend-urls/",
      expect.objectContaining({
        credentials: "include",
        headers: expect.objectContaining({
          Accept: "application/json",
          "X-Wagtail-Unveil-Report-Access": "signed-report-token",
        }),
      }),
    );
  });

  test("report data loader does not send the signed report access header when absent", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/backend-urls/",
      reportKind: "backend",
    });

    const fetchMock = stubFetchResponse({
      count: 0,
      metadata: {
        total_count: 0,
        testable_count: 0,
        untestable_count: 0,
      },
      urls: [],
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(fetchMock).toHaveBeenCalledWith(
      "/unveil/api/backend-urls/",
      expect.objectContaining({
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      }),
    );
  });

  test("platform report sends the signed report access header and renders sectioned tables", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
      reportAccessToken: "signed-report-token",
    });

    const fetchMock = stubFetchResponse({
      platform: {
        runtime: {
          python_version: "3.12.1",
          python_implementation: "CPython",
          django_version: "5.2.1",
          wagtail_version: "7.3.1",
        },
        python_dependencies: {
          source: {
            path: "pyproject.toml",
            format: "pyproject.toml",
          },
          packages: [
            {
              name: "Django",
              specifier: ">=5.2",
              installed_version: "5.2.1",
              is_installed: true,
              source_kind: "runtime",
              source_name: null,
            },
            {
              name: "mkdocs",
              specifier: ">=1.6.0",
              installed_version: "",
              is_installed: false,
              source_kind: "group",
              source_name: "docs",
            },
          ],
        },
        warnings: ["Dependency manifest is missing or inaccessible."],
      },
      metadata: {
        api_version: "v1",
        api_lifecycle: {
          status: "stable",
        },
        generated_at: "2026-04-08T20:27:18.791636+00:00",
        package_version: "0.1.0a5",
      },
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(
      fetchMock.mock.calls[0][1].headers["X-Wagtail-Unveil-Report-Access"],
    ).toBe("signed-report-token");
    expect(document.body.dataset.reportState).toBe("ready");
    expect(document.getElementById("report-total").textContent).toBe("2");
    expect(document.getElementById("report-testable").textContent).toBe("1");
    expect(document.getElementById("report-untestable").textContent).toBe("1");
    expect(document.getElementById("report-warning-count").textContent).toBe(
      "1",
    );
    expect(
      document.querySelector("#platform-runtime-body tr td:last-child")
        .textContent,
    ).toBe("3.12.1");
    expect(document.querySelectorAll("#platform-packages-body tr").length).toBe(
      2,
    );
    expect(
      document.querySelector(
        "#platform-metadata-body tr:last-child td:last-child",
      ).textContent,
    ).toBe("0.1.0a5");
  });

  test("platform report renders empty states for warnings and dependencies", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
    });

    stubFetchResponse({
      platform: {
        runtime: {
          python_version: "3.12.1",
          python_implementation: "CPython",
          django_version: "5.2.1",
          wagtail_version: "7.3.1",
        },
        python_dependencies: {
          source: {
            path: "",
            format: null,
          },
          packages: [],
        },
        warnings: [],
      },
      metadata: {
        api_version: "v1",
        api_lifecycle: {
          status: "stable",
        },
        generated_at: "2026-04-08T20:27:18.791636+00:00",
        package_version: "0.1.0a5",
      },
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(
      document.querySelector("#platform-warnings-body td").textContent,
    ).toBe("No warnings.");
    expect(
      document.querySelector("#platform-packages-body td").textContent,
    ).toBe("No dependencies found.");
  });

  test("platform report shows the error screen for invalid payload shape", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
    });

    stubFetchResponse({
      metadata: {
        api_version: "v1",
      },
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(document.body.dataset.reportState).toBe("error");
    expect(document.getElementById("report-error-message").textContent).toBe(
      "Report data response was not valid JSON.",
    );
  });
});
