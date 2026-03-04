import { beforeEach, describe, expect, test } from "vitest";

import {
  loadBundleScript,
  resetReportDom,
  stubFetchResponse,
} from "./helpers/reportHarness.js";

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

    await Promise.resolve();
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(window.UnveilReport).toBeTruthy();
    expect(document.body.dataset.reportState).toBe("ready");
    expect(document.querySelectorAll("tbody tr").length).toBe(1);
    expect(document.querySelector(".test-btn")).toBeTruthy();
  });
});
