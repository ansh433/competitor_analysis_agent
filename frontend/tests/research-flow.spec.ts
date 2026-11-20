import { type Page, expect, test } from "@playwright/test";

function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}@example.com`;
}

async function signUp(page: Page, email: string): Promise<void> {
  await page.goto("/signup");
  await page.getByLabel("Full name").fill("Playwright Analyst");
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("integrated browser research password");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

async function createWorkspace(page: Page, name: string): Promise<string> {
  await page.goto("/workspaces");
  await page.getByLabel("Name").fill(name);
  await page.getByLabel("Description").fill("Browser integration workspace");
  await page.getByRole("button", { name: "Create workspace" }).click();
  const workspaceLink = page.getByRole("link", { name: new RegExp(name) });
  await expect(workspaceLink).toBeVisible();
  const href = await workspaceLink.getAttribute("href");
  if (!href) throw new Error("Workspace link did not have an href");
  return href.split("/").at(-1) ?? "";
}

test("signup, login, streamed research, citations, comparison, and branching", async ({
  page,
}) => {
  const email = uniqueEmail("research-flow");
  await signUp(page, email);
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("integrated browser research password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

  await createWorkspace(page, "Competitive launch");
  await page.goto("/research");
  await page
    .getByLabel("Workspace")
    .selectOption({ label: "Competitive launch" });
  await page.getByLabel("Company name or website").fill("Acme Collaboration");
  await page
    .getByLabel("Research objective")
    .fill(
      "Assess product differentiation and pricing for a launch strategy decision.",
    );
  await page.getByRole("button", { name: "Begin research" }).click();

  await expect(
    page.getByRole("heading", { name: /competitor intelligence dossier/i }),
  ).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText("Complete", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Comparison artifact" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Evidence ledger/i }),
  ).toBeVisible();

  await page
    .getByRole("button", { name: /Evidence [0-9a-f]+/ })
    .first()
    .click();
  await expect(
    page.getByRole("dialog").getByText("Evidence detail"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close evidence" }).click();
  await page.getByRole("button", { name: "Branch investigation" }).click();
  await expect(page.getByText(/Branch [0-9a-f]+ created/)).toBeVisible();
});

test("landing page sample matrix and account entry are interactive", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "Know where a company stands before you decide.",
    }),
  ).toBeVisible();

  await page.getByRole("link", { name: "Sign up" }).click();
  await expect(
    page.getByRole("heading", { name: "Create an account" }),
  ).toBeVisible();
});

test("signed-in landing header shows user initials", async ({ page }) => {
  await signUp(page, uniqueEmail("landing-avatar"));
  await page.goto("/");
  await expect(
    page.getByRole("link", { name: "Open dashboard for Playwright Analyst" }),
  ).toHaveText("PA");
});

test("authentication pages share mobile layout and password controls", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/login");
  const loginHeading = page.getByRole("heading", { name: "Sign in" });
  const loginEmail = page.getByLabel("Email address");
  const loginPassword = page.getByLabel("Password", { exact: true });
  await expect(loginHeading).toBeVisible();
  await expect(page.getByRole("link", { name: "Compass" })).toHaveCount(0);
  await page.getByRole("button", { name: "Show password" }).click();
  await expect(loginPassword).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Hide password" }).click();
  await expect(loginPassword).toHaveAttribute("type", "password");
  const loginHeadingBox = await loginHeading.boundingBox();
  const loginEmailBox = await loginEmail.boundingBox();
  const loginHeadingSize = await loginHeading.evaluate(
    (element) => getComputedStyle(element).fontSize,
  );

  await page.goto("/signup");
  const signupHeading = page.getByRole("heading", {
    name: "Create an account",
  });
  const signupEmail = page.getByLabel("Email address");
  await expect(signupHeading).toBeVisible();
  await expect(page.getByRole("link", { name: "Compass" })).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Show password" }),
  ).toBeVisible();
  const signupHeadingBox = await signupHeading.boundingBox();
  const signupEmailBox = await signupEmail.boundingBox();
  const signupHeadingSize = await signupHeading.evaluate(
    (element) => getComputedStyle(element).fontSize,
  );

  expect(signupHeadingBox?.y).toBeCloseTo(loginHeadingBox?.y ?? 0, 0);
  expect(signupHeadingSize).toBe(loginHeadingSize);
  expect(signupEmailBox?.height).toBeCloseTo(loginEmailBox?.height ?? 0, 0);
});

test("dossier keeps evidence readable and matrices bounded across screens", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1536, height: 1000 });
  await signUp(page, uniqueEmail("dossier-layout"));
  const evidenceId = "d81b2be1-2222-4444-8888-123456789abc";
  const evidence = {
    id: evidenceId,
    claim: "The company publishes its product catalogue.",
    source_url: "https://example.com/products",
    confidence: 0.9,
    fact_classification: "sourced_fact",
  };
  await page.route("**/api/v1/companies/layout-company", (route) =>
    route.fulfill({
      json: {
        id: "layout-company",
        workspace_id: "layout-workspace",
        display_name: "Evenflow Brands",
        domain: "example.com",
        research_status: "completed",
      },
    }),
  );
  await page.route(
    "**/api/v1/companies/layout-company/research-runs/latest",
    (route) =>
      route.fulfill({
        json: {
          id: "layout-run",
          status: "completed",
          evidence: [evidence],
          coverage_score: 0.65,
          confidence_score: 0.85,
          final_report: `# Competitor intelligence dossier
## 1. Executive summary
A deliberately concise assessment supported by the evidence ledger.
## 7. Feature comparison matrix
| Dimension | Evenflow | Company B | Company C | Company D |
| --- | --- | --- | --- | --- |
| Catalogue | Published | Published | Unavailable | Published |
## 15. Evidence ledger
<a id="evidence-${evidenceId}"></a>
**Sourced fact**: The company publishes its product catalogue.
## 16. Research notes
Pricing information remains unavailable.`,
        },
      }),
  );
  await page.route(`**/api/v1/evidence/${evidenceId}`, (route) =>
    route.fulfill({ json: evidence }),
  );
  await page.goto("/companies/layout-company");
  const summary = page.locator("#dossier-section-1");
  const matrix = page.locator("#dossier-section-7");
  await expect(
    matrix.getByRole("cell", { name: "Published", exact: true }).first(),
  ).toBeVisible();
  const summaryBox = await summary.boundingBox();
  const matrixBox = await matrix.boundingBox();
  expect(matrixBox?.width).toBeGreaterThan((summaryBox?.width ?? 0) + 150);
  await expect(page.getByText("65%", { exact: true })).toBeVisible();
  await expect(page.locator("#dossier-section-16")).toContainText(
    "Pricing information remains unavailable.",
  );
  await expect(page.getByText("<a id=", { exact: false })).toHaveCount(0);
  await page.getByRole("button", { name: /^Evidence 1:/ }).click();
  await expect(page.getByRole("dialog")).toContainText("90%");
  await page.getByRole("button", { name: "Close evidence" }).click();
  await page.screenshot({
    path: "/tmp/compass-dossier-desktop.png",
    fullPage: true,
  });

  await page.setViewportSize({ width: 390, height: 844 });
  const frame = matrix.getByRole("region", { name: "Comparison table" });
  await expect(frame).toBeVisible();
  expect(
    await frame.evaluate(
      (element) => element.scrollWidth > element.clientWidth,
    ),
  ).toBe(true);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  const dimensionHeader = frame.getByRole("columnheader", {
    name: "Dimension",
  });
  const dimensionCell = frame.getByRole("cell", { name: "Catalogue" });
  const headerXBeforeScroll = (await dimensionHeader.boundingBox())?.x;
  const cellXBeforeScroll = (await dimensionCell.boundingBox())?.x;
  await frame.evaluate((element) => {
    element.scrollLeft = 320;
  });
  const headerXAfterScroll = (await dimensionHeader.boundingBox())?.x;
  const cellXAfterScroll = (await dimensionCell.boundingBox())?.x;
  expect(headerXAfterScroll).toBeCloseTo(headerXBeforeScroll ?? 0, 0);
  expect(cellXAfterScroll).toBeCloseTo(cellXBeforeScroll ?? 0, 0);
  await expect(dimensionHeader).toHaveCSS("position", "sticky");
  await expect(dimensionCell).toHaveCSS("position", "sticky");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("link", { name: "Workspaces", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close navigation" }).click();
  await page.screenshot({
    path: "/tmp/compass-dossier-mobile.png",
    fullPage: true,
  });
});

test("cross-user workspace access is denied", async ({ page }) => {
  await signUp(page, uniqueEmail("owner"));
  const workspaceId = await createWorkspace(page, "Private mandate");
  await page.getByRole("button", { name: "Sign out" }).click();
  await signUp(page, uniqueEmail("outsider"));

  const status = await page.evaluate(async (id) => {
    const token = window.localStorage.getItem("competitor-intelligence-token");
    const response = await fetch(`/api/v1/workspaces/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.status;
  }, workspaceId);
  expect(status).toBe(404);
});

test("quota exhausted state disables new research", async ({ page }) => {
  await signUp(page, uniqueEmail("quota-ui"));
  const workspaceId = await createWorkspace(page, "Quota mandate");
  const statuses = await page.evaluate(
    async ({ workspaceId: id }) => {
      const token = window.localStorage.getItem(
        "competitor-intelligence-token",
      );
      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };
      const responses: number[] = [];
      for (let index = 0; index < 5; index += 1) {
        const response = await fetch("/api/v1/research-runs", {
          method: "POST",
          headers,
          body: JSON.stringify({
            workspace_id: id,
            company_name_or_url: `Quota UI Company ${index}`,
            objective:
              "Assess this company while exercising the configured daily quota boundary.",
            model_tier: "standard",
          }),
        });
        responses.push(response.status);
      }
      return responses;
    },
    { workspaceId },
  );
  expect(statuses).toEqual([201, 201, 201, 201, 201]);

  await page.goto("/research");
  await expect(page.getByRole("alert")).toContainText("allowance exhausted");
  await expect(
    page.getByRole("button", { name: "Begin research" }),
  ).toBeDisabled();
});
