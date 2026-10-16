import { type Page, expect, test } from "@playwright/test";

function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}@example.com`;
}

async function signUp(page: Page, email: string): Promise<void> {
  await page.goto("/signup");
  await page.getByLabel("Full name").fill("Playwright Analyst");
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password")
    .fill("integrated browser research password");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(
    page.getByRole("heading", { name: "Research that shows its work." }),
  ).toBeVisible();
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
    .getByLabel("Password")
    .fill("integrated browser research password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByRole("heading", { name: "Research that shows its work." }),
  ).toBeVisible();

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
    page.getByRole("heading", { name: "Evidence records" }),
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
