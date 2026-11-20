const COMPANY_PREFILL_KEY = "compass-research-company-prefill";

/** Save a company entry while the user moves into the research flow. */
export function storeResearchCompanyPrefill(company: string): void {
  window.sessionStorage.setItem(COMPANY_PREFILL_KEY, company);
}

/** Read the pending company entry without consuming it. */
export function getResearchCompanyPrefill(): string {
  return window.sessionStorage.getItem(COMPANY_PREFILL_KEY) ?? "";
}

/** Clear the pending company entry once a research run starts. */
export function clearResearchCompanyPrefill(): void {
  window.sessionStorage.removeItem(COMPANY_PREFILL_KEY);
}
