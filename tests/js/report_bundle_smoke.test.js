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
});
