import { beforeEach, describe, expect, test, vi } from "vitest";

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

function createPlatformPayload(packages = []) {
  return {
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
        packages,
      },
      warnings: [],
    },
    metadata: {
      api_version: "v1",
      api_lifecycle: {
        status: "stable",
      },
      generated_at: "2026-04-08T20:27:18.791636+00:00",
      package_version: "0.1.0a6",
    },
  };
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
      ...createPlatformPayload([
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
      ]),
      platform: {
        ...createPlatformPayload([]).platform,
        warnings: ["Dependency manifest is missing or inaccessible."],
        python_dependencies: {
          ...createPlatformPayload([]).platform.python_dependencies,
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
      document.querySelector("#platform-packages-body tr .platform-pypi-cell")
        .textContent,
    ).toContain("—");
    expect(
      document.querySelector(
        "#platform-metadata-body tr:last-child td:last-child",
      ).textContent,
    ).toBe("0.1.0a6");
  });

  test("platform report renders empty states for warnings and dependencies", async () => {
    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
    });

    stubFetchResponse(createPlatformPayload([]));

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

  test("platform report only starts PyPI lookup after button click", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () =>
          createPlatformPayload([
            {
              name: "Django",
              specifier: ">=5.2",
              installed_version: "5.2.1",
              is_installed: true,
              source_kind: "runtime",
              source_name: null,
            },
          ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          info: {
            version: "5.2.2",
          },
        }),
      });

    globalThis.fetch = fetchMock;
    window.fetch = fetchMock;

    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    expect(fetchMock).toHaveBeenCalledTimes(1);

    document.getElementById("platform-pypi-lookup-button").click();
    await waitForRender();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[1][0]).toBe(
      "https://pypi.org/pypi/django/json",
    );
    expect(
      document.querySelector("#platform-packages-body tr .platform-pypi-cell")
        .textContent,
    ).toContain("5.2.2");
    expect(
      document.querySelector("#platform-packages-body tr .platform-pypi-cell")
        .textContent,
    ).toContain("Different");
    expect(
      document.querySelector("#platform-packages-body tr .platform-pypi-cell"),
    ).not.toBeNull();
    expect(
      document
        .querySelector("#platform-packages-body tr .platform-pypi-cell")
        .classList.contains("platform-pypi-warning"),
    ).toBe(true);
  });

  test("platform report dedupes package lookups and handles mixed PyPI outcomes", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () =>
          createPlatformPayload([
            {
              name: "Django",
              specifier: ">=5.2",
              installed_version: "5.2.1",
              is_installed: true,
              source_kind: "runtime",
              source_name: null,
            },
            {
              name: "Django",
              specifier: ">=5.2",
              installed_version: "5.2.1",
              is_installed: true,
              source_kind: "group",
              source_name: "dev",
            },
            {
              name: "missing-project",
              specifier: "*",
              installed_version: "",
              is_installed: false,
              source_kind: "group",
              source_name: "docs",
            },
            {
              name: "broken-project",
              specifier: "*",
              installed_version: "",
              is_installed: false,
              source_kind: "group",
              source_name: "docs",
            },
          ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          info: {
            version: "5.2.1",
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({}),
      })
      .mockRejectedValueOnce(new Error("network failure"));

    globalThis.fetch = fetchMock;
    window.fetch = fetchMock;

    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    const button = document.getElementById("platform-pypi-lookup-button");

    button.click();
    expect(button.disabled).toBe(true);
    await waitForRender();
    await waitForRender();

    expect(button.disabled).toBe(false);
    expect(fetchMock).toHaveBeenCalledTimes(4);

    const rows = Array.from(
      document.querySelectorAll("#platform-packages-body tr"),
    );

    expect(rows[0].querySelector(".platform-pypi-cell").textContent).toContain(
      "5.2.1",
    );
    expect(rows[0].querySelector(".platform-pypi-cell").textContent).toContain(
      "Latest",
    );
    expect(
      rows[0]
        .querySelector(".platform-pypi-cell")
        .classList.contains("platform-pypi-success"),
    ).toBe(true);
    expect(rows[1].querySelector(".platform-pypi-cell").textContent).toContain(
      "5.2.1",
    );
    expect(rows[1].querySelector(".platform-pypi-cell").textContent).toContain(
      "Latest",
    );
    expect(rows[2].querySelector(".platform-pypi-cell").textContent).toContain(
      "Not on PyPI",
    );
    expect(
      rows[2]
        .querySelector(".platform-pypi-cell")
        .classList.contains("platform-pypi-danger"),
    ).toBe(true);
    expect(rows[3].querySelector(".platform-pypi-cell").textContent).toContain(
      "Lookup failed",
    );
    expect(
      rows[3]
        .querySelector(".platform-pypi-cell")
        .classList.contains("platform-pypi-danger"),
    ).toBe(true);
  });

  test("platform report normalizes equivalent package names for a single PyPI lookup", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () =>
          createPlatformPayload([
            {
              name: "Django",
              specifier: ">=5.2",
              installed_version: "5.2.1",
              is_installed: true,
              source_kind: "runtime",
              source_name: null,
            },
            {
              name: "django",
              specifier: ">=5.2",
              installed_version: "5.2.1",
              is_installed: true,
              source_kind: "group",
              source_name: "dev",
            },
            {
              name: "my_pkg",
              specifier: ">=1.0",
              installed_version: "1.0.0",
              is_installed: true,
              source_kind: "group",
              source_name: "docs",
            },
            {
              name: "my-pkg",
              specifier: ">=1.0",
              installed_version: "1.0.0",
              is_installed: true,
              source_kind: "optional",
              source_name: "extras",
            },
          ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          info: {
            version: "5.2.1",
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          info: {
            version: "1.1.0",
          },
        }),
      });

    globalThis.fetch = fetchMock;
    window.fetch = fetchMock;

    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    document.getElementById("platform-pypi-lookup-button").click();
    await waitForRender();
    await waitForRender();

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toBe(
      "https://pypi.org/pypi/django/json",
    );
    expect(fetchMock.mock.calls[2][0]).toBe(
      "https://pypi.org/pypi/my-pkg/json",
    );

    const rows = Array.from(
      document.querySelectorAll("#platform-packages-body tr"),
    );

    expect(rows[0].querySelector(".platform-pypi-cell").textContent).toContain(
      "5.2.1",
    );
    expect(rows[1].querySelector(".platform-pypi-cell").textContent).toContain(
      "5.2.1",
    );
    expect(rows[0].querySelector(".platform-pypi-cell").textContent).toContain(
      "Latest",
    );
    expect(rows[1].querySelector(".platform-pypi-cell").textContent).toContain(
      "Latest",
    );
    expect(rows[2].querySelector(".platform-pypi-cell").textContent).toContain(
      "1.1.0",
    );
    expect(rows[3].querySelector(".platform-pypi-cell").textContent).toContain(
      "1.1.0",
    );
    expect(rows[2].querySelector(".platform-pypi-cell").textContent).toContain(
      "Different",
    );
    expect(rows[3].querySelector(".platform-pypi-cell").textContent).toContain(
      "Different",
    );
  });

  test("platform report updates completed PyPI rows before slower lookups finish", async () => {
    let resolveDjango;
    let resolveWagtail;
    const djangoPromise = new Promise((resolve) => {
      resolveDjango = resolve;
    });
    const wagtailPromise = new Promise((resolve) => {
      resolveWagtail = resolve;
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () =>
          createPlatformPayload([
            {
              name: "Django",
              specifier: ">=5.2",
              installed_version: "5.2.1",
              is_installed: true,
              source_kind: "runtime",
              source_name: null,
            },
            {
              name: "wagtail",
              specifier: ">=7.0",
              installed_version: "7.0.0",
              is_installed: true,
              source_kind: "runtime",
              source_name: null,
            },
          ]),
      })
      .mockImplementationOnce(() => djangoPromise)
      .mockImplementationOnce(() => wagtailPromise);

    globalThis.fetch = fetchMock;
    window.fetch = fetchMock;

    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    document.getElementById("platform-pypi-lookup-button").click();
    await waitForRender();

    resolveDjango({
      ok: true,
      status: 200,
      json: async () => ({
        info: {
          version: "5.2.1",
        },
      }),
    });
    await waitForRender();

    const rows = Array.from(
      document.querySelectorAll("#platform-packages-body tr"),
    );

    expect(rows[0].querySelector(".platform-pypi-cell").textContent).toContain(
      "5.2.1",
    );
    expect(rows[0].querySelector(".platform-pypi-cell").textContent).toContain(
      "Latest",
    );
    expect(rows[1].querySelector(".platform-pypi-cell").textContent).toContain(
      "Loading",
    );

    resolveWagtail({
      ok: true,
      status: 200,
      json: async () => ({
        info: {
          version: "7.1.0",
        },
      }),
    });
    await waitForRender();

    expect(rows[1].querySelector(".platform-pypi-cell").textContent).toContain(
      "7.1.0",
    );
    expect(rows[1].querySelector(".platform-pypi-cell").textContent).toContain(
      "Different",
    );
  });

  test("platform report marks rows as unknown when no installed version is available", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () =>
          createPlatformPayload([
            {
              name: "mkdocs",
              specifier: ">=1.6.0",
              installed_version: "",
              is_installed: false,
              source_kind: "group",
              source_name: "docs",
            },
          ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          info: {
            version: "1.7.0",
          },
        }),
      });

    globalThis.fetch = fetchMock;
    window.fetch = fetchMock;

    resetReportDom({
      apiUrl: "/unveil/api/v1/platform/",
      reportKind: "platform",
    });

    loadBundleScript();
    document.dispatchEvent(new Event("DOMContentLoaded"));
    await waitForRender();

    document.getElementById("platform-pypi-lookup-button").click();
    await waitForRender();

    expect(
      document.querySelector("#platform-packages-body tr .platform-pypi-cell")
        .textContent,
    ).toContain("Unknown");
    expect(
      document.querySelector("#platform-packages-body tr .platform-pypi-cell"),
    ).not.toBeNull();
    expect(
      document
        .querySelector("#platform-packages-body tr .platform-pypi-cell")
        .classList.contains("platform-pypi-warning"),
    ).toBe(true);
  });
});
