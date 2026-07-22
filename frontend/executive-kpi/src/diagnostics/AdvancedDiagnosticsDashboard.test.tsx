import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  AdvancedDiagnosticsDashboard,
  type AdvancedDiagnosticsState,
} from "./AdvancedDiagnosticsDashboard";

const HREFS = { advancedDiagnostics: "/advanced-diagnostics", scanWorkspace: "/scan-workspace" };

const SAVED_SCAN_OPTIONS = [
  {
    scanId: "scan id/42",
    company: "Acme Corp",
    title: "Staff Engineer",
    resume: "resume_v2",
    status: "Reviewed",
    primary: "Acme Corp / Staff Engineer",
    secondary: "Resume: resume_v2 · Reviewed",
  },
];

const HUB_STATE: AdvancedDiagnosticsState = {
  mode: "hub",
  savedScanOptions: SAVED_SCAN_OPTIONS,
  selectedScanId: "",
  context: null,
  hrefs: HREFS,
};

const EMPTY_STATE: AdvancedDiagnosticsState = {
  mode: "empty",
  savedScanOptions: [],
  selectedScanId: "",
  context: null,
  hrefs: HREFS,
};

const INVALID_STATE: AdvancedDiagnosticsState = {
  mode: "invalid",
  savedScanOptions: SAVED_SCAN_OPTIONS,
  selectedScanId: "not-a-real-scan",
  context: null,
  hrefs: HREFS,
};

const CONTEXT_STATE: AdvancedDiagnosticsState = {
  mode: "context",
  savedScanOptions: SAVED_SCAN_OPTIONS,
  selectedScanId: "scan id/42",
  context: {
    company: "Acme Corp",
    title: "Staff Engineer",
    resume: "resume v2",
    status: "Reviewed",
    contextId: "scan-42-report.json",
    backToScanHref: "/scan-workspace?saved_scan_id=scan+id%2F42",
  },
  hrefs: HREFS,
};

const STANDALONE_CHECKBOX_IDS = [
  "scanWorkspaceLiveTailoringSuggestionToggle",
  "scanWorkspaceLiveExactChangeProposalToggle",
];

const ALL_CONTROL_IDS = [
  ...STANDALONE_CHECKBOX_IDS,
  "scanWorkspaceManualExactChangeAcceptanceToggle",
  "scanWorkspaceAcceptedExactChangeProposalIds",
  "scanWorkspaceGuardedResumeCopyArtifactToggle",
  "scanWorkspaceApprovedChangePlanId",
  "scanWorkspaceGuardedResumeCopyArtifactVerificationToggle",
  "scanWorkspaceGuardedResumeCopyArtifactId",
  "scanWorkspaceVerifiedArtifactOperatorReviewPacketToggle",
  "scanWorkspaceVerifiedArtifactOperatorReviewArtifactId",
  "scanWorkspaceVerifiedArtifactOperatorDecisionToggle",
  "scanWorkspaceVerifiedArtifactOperatorDecisionPacketId",
  "scanWorkspaceVerifiedArtifactOperatorDecisionArtifactId",
  "scanWorkspaceVerifiedArtifactOperatorDecisionValue",
  "scanWorkspaceApplicationReadinessPacketToggle",
  "scanWorkspaceApplicationReadinessDecisionId",
  "scanWorkspaceApplicationReadinessReviewPacketId",
  "scanWorkspaceApplicationReadinessArtifactId",
  "scanWorkspaceManualApplicationHandoffPacketToggle",
  "scanWorkspaceManualHandoffReadinessPacketId",
  "scanWorkspaceManualHandoffArtifactId",
  "scanWorkspaceHandoffAuditTrailToggle",
  "scanWorkspaceHandoffAuditHandoffPacketId",
  "scanWorkspaceHandoffAuditReadinessPacketId",
  "scanWorkspaceHandoffAuditArtifactId",
  "scanWorkspaceSafetyBoundarySummaryToggle",
  "scanWorkspaceSafetyBoundaryAuditTrailId",
  "scanWorkspaceSafetyBoundaryHandoffPacketId",
  "scanWorkspaceSafetyBoundaryReadinessPacketId",
  "scanWorkspaceSafetyBoundaryArtifactId",
  "scanWorkspaceWorkflowReadinessCheckpointToggle",
  "scanWorkspaceWorkflowReadinessSummaryId",
  "scanWorkspaceWorkflowReadinessAuditTrailId",
  "scanWorkspaceWorkflowReadinessHandoffPacketId",
  "scanWorkspaceWorkflowReadinessReadinessPacketId",
  "scanWorkspaceWorkflowReadinessArtifactId",
];

const ALL_READBACK_IDS = [
  "scanWorkspaceJdLlmReadback",
  "scanWorkspaceTailoringLlmReadback",
  "scanWorkspaceExactChangeLlmReadback",
  "scanWorkspaceManualExactChangeAcceptanceReadback",
  "scanWorkspaceGuardedResumeCopyArtifactReadback",
  "scanWorkspaceGuardedResumeCopyArtifactVerificationReadback",
  "scanWorkspaceVerifiedArtifactOperatorReviewPacketReadback",
  "scanWorkspaceVerifiedArtifactOperatorDecisionReadback",
  "scanWorkspaceApplicationReadinessPacketReadback",
  "scanWorkspaceManualApplicationHandoffPacketReadback",
  "scanWorkspaceHandoffAuditTrailReadback",
  "scanWorkspaceSafetyBoundarySummaryReadback",
  "scanWorkspaceWorkflowReadinessCheckpointReadback",
  "scanWorkspaceAgenticWorkflowIntegrationReadback",
  "scanWorkspaceProductionReadinessCheckpointReadback",
];

const SECTION_IDS = [
  "advancedDiagnosticsSectionGeneration",
  "advancedDiagnosticsSectionArtifactSafety",
  "advancedDiagnosticsSectionReviewDecision",
  "advancedDiagnosticsSectionManualHandoff",
  "advancedDiagnosticsSectionReadbacks",
];

function selectSavedScanOption() {
  fireEvent.click(screen.getByRole("button", { name: /saved scan/i }));
  fireEvent.click(screen.getByRole("option", { name: /Acme Corp \/ Staff Engineer/ }));
}

describe("AdvancedDiagnosticsDashboard — hub mode", () => {

  it("renders the searchable saved-scan selector", () => {
    render(<AdvancedDiagnosticsDashboard state={HUB_STATE} />);
    expect(screen.getByText("Choose a saved scan")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /saved scan/i }));
    expect(screen.getByPlaceholderText(/search saved scan/i)).toBeInTheDocument();
  });

  it("supplies the advanced-diagnostics-scan-menu portal class to the portaled menu", () => {
    render(<AdvancedDiagnosticsDashboard state={HUB_STATE} />);
    fireEvent.click(screen.getByRole("button", { name: /saved scan/i }));
    const menu = screen.getByRole("listbox");
    expect(menu).toHaveClass("shared-filter-select__menu");
    expect(menu).toHaveClass("advanced-diagnostics-scan-menu");
  });

  it("disables Open diagnostics before a scan is selected", () => {
    render(<AdvancedDiagnosticsDashboard state={HUB_STATE} />);
    expect(screen.getByRole("button", { name: "Open diagnostics" })).toBeDisabled();
  });

  it("enables Open diagnostics once a scan is selected", () => {
    render(<AdvancedDiagnosticsDashboard state={HUB_STATE} />);
    selectSavedScanOption();
    expect(screen.getByRole("button", { name: "Open diagnostics" })).toBeEnabled();
  });

  it("navigates with an encoded saved_scan_id query parameter", () => {
    const navigate = vi.fn();
    render(<AdvancedDiagnosticsDashboard state={HUB_STATE} navigate={navigate} />);
    selectSavedScanOption();
    fireEvent.click(screen.getByRole("button", { name: "Open diagnostics" }));
    expect(navigate).toHaveBeenCalledWith(
      `/advanced-diagnostics?saved_scan_id=${encodeURIComponent("scan id/42")}`,
    );
  });

  it("does not render either context action", () => {
    render(<AdvancedDiagnosticsDashboard state={HUB_STATE} />);
    expect(screen.queryByRole("link", { name: "Back to scan" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Change scan" })).not.toBeInTheDocument();
  });
});

describe("AdvancedDiagnosticsDashboard — empty mode", () => {

  it("renders the no-saved-scans empty state", () => {
    render(<AdvancedDiagnosticsDashboard state={EMPTY_STATE} />);
    expect(screen.getByText("No saved scans available")).toBeInTheDocument();
  });

  it("links Open New Scan to /scan-workspace", () => {
    render(<AdvancedDiagnosticsDashboard state={EMPTY_STATE} />);
    expect(screen.getByRole("link", { name: "Open New Scan" })).toHaveAttribute(
      "href",
      "/scan-workspace",
    );
  });
});

describe("AdvancedDiagnosticsDashboard — invalid mode", () => {

  it("renders the neutral scan-context-unavailable state", () => {
    render(<AdvancedDiagnosticsDashboard state={INVALID_STATE} />);
    expect(screen.getByText("Scan context unavailable")).toBeInTheDocument();
    expect(
      screen.getByText("This scan could not be found or is not available to this account."),
    ).toBeInTheDocument();
  });

  it("does not render any workflow diagnostic controls", () => {
    render(<AdvancedDiagnosticsDashboard state={INVALID_STATE} />);
    for (const id of ALL_CONTROL_IDS) {
      expect(document.getElementById(id)).toBeNull();
    }
    expect(document.getElementById("scanWorkspaceAdvancedDiagnostics")).toBeNull();
  });

  it("does not render Back to scan", () => {
    render(<AdvancedDiagnosticsDashboard state={INVALID_STATE} />);
    expect(screen.queryByRole("link", { name: "Back to scan" })).not.toBeInTheDocument();
  });
});

describe("AdvancedDiagnosticsDashboard — context mode", () => {

  it("renders company, title, resume, status, and context ID", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(screen.getByText("Acme Corp / Staff Engineer")).toBeInTheDocument();
    expect(screen.getByText("resume v2")).toBeInTheDocument();
    expect(screen.getByText("Reviewed")).toBeInTheDocument();
    expect(screen.getByText("scan-42-report.json")).toBeInTheDocument();
  });

  it("uses the server-provided Back to scan href", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    for (const link of screen.getAllByRole("link", { name: "Back to scan" })) {
      expect(link).toHaveAttribute("href", CONTEXT_STATE.context!.backToScanHref);
    }
  });

  it("links Change scan to /advanced-diagnostics", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    for (const link of screen.getAllByRole("link", { name: "Change scan" })) {
      expect(link).toHaveAttribute("href", "/advanced-diagnostics");
    }
  });

  it("renders Back to scan and Change scan inside the Scan Context card, not the main header", () => {
    const { container } = render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    const header = screen.getByRole("banner");
    const contextCard = container.querySelector(".advanced-diagnostics-context-hero");
    expect(contextCard).not.toBeNull();

    const backLink = screen.getByRole("link", { name: "Back to scan" });
    const changeLink = screen.getByRole("link", { name: "Change scan" });
    expect(contextCard).toContainElement(backLink);
    expect(contextCard).toContainElement(changeLink);
    expect(header).not.toContainElement(backLink);
    expect(header).not.toContainElement(changeLink);
  });

  it("renders the Admin only and Read-only badges", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(screen.getByText("Admin only")).toBeInTheDocument();
    expect(screen.getByText("Read-only")).toBeInTheDocument();
  });

  it("renders all four configurable diagnostic groups", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(screen.getByText("Generation diagnostics")).toBeInTheDocument();
    expect(screen.getByText("Resume artifact safety")).toBeInTheDocument();
    expect(screen.getByText("Review packet/operator decision")).toBeInTheDocument();
    expect(screen.getByText("Manual handoff/readiness")).toBeInTheDocument();
  });

  it("renders every current control ID exactly once", () => {
    const { container } = render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    for (const id of ALL_CONTROL_IDS) {
      expect(container.querySelectorAll(`[id="${id}"]`)).toHaveLength(1);
    }
  });

  it("renders all 15 readback rows", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(screen.getByText("Live JD LLM")).toBeInTheDocument();
    expect(screen.getByText("Demo readiness")).toBeInTheDocument();
    for (const id of ALL_READBACK_IDS) {
      expect(document.getElementById(id)).not.toBeNull();
    }
  });

  it("renders exactly thirteen Default off badges", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(screen.getAllByText("Default off")).toHaveLength(13);
  });

  it("renders exactly two Waiting badges", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(screen.getAllByText("Waiting")).toHaveLength(2);
  });

  it("renders every current readback ID exactly once", () => {
    const { container } = render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    for (const id of ALL_READBACK_IDS) {
      expect(container.querySelectorAll(`[id="${id}"]`)).toHaveLength(1);
    }
  });

  it("keeps aria-live=\"polite\" on every readback row", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    for (const id of ALL_READBACK_IDS) {
      expect(document.getElementById(id)).toHaveAttribute("aria-live", "polite");
    }
  });

  it("resets checkbox, text, and select local state on Clear selections", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    const checkbox = screen.getByLabelText("Live tailoring suggestions") as HTMLInputElement;
    const textField = document.getElementById(
      "scanWorkspaceApprovedChangePlanId",
    ) as HTMLInputElement;
    const selectField = document.getElementById(
      "scanWorkspaceVerifiedArtifactOperatorDecisionValue",
    ) as HTMLSelectElement;

    fireEvent.click(checkbox);
    fireEvent.change(textField, { target: { value: "plan-123" } });
    fireEvent.change(selectField, { target: { value: "accepted" } });
    expect(checkbox.checked).toBe(true);
    expect(textField.value).toBe("plan-123");
    expect(selectField.value).toBe("accepted");

    fireEvent.click(screen.getByRole("button", { name: "Clear selections" }));
    expect(checkbox.checked).toBe(false);
    expect(textField.value).toBe("");
    expect(selectField.value).toBe("");
  });

  it("does not change the rendered scan context when clearing selections", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    fireEvent.click(screen.getByRole("button", { name: "Clear selections" }));
    expect(screen.getByText("Acme Corp / Staff Engineer")).toBeInTheDocument();
    expect(screen.getByText("scan-42-report.json")).toBeInTheDocument();
  });

  it("keeps Run selected diagnostics permanently disabled", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(screen.getByRole("button", { name: "Run selected diagnostics" })).toBeDisabled();
  });

  it("uses the exact disabled-execution title", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(screen.getByRole("button", { name: "Run selected diagnostics" })).toHaveAttribute(
      "title",
      "Execution is not enabled yet. Selections are for admin review only.",
    );
  });

  it("keeps the required safety copy present", () => {
    const { container } = render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    const text = container.textContent || "";
    expect(text).toContain("These do not apply to jobs automatically.");
    expect(text).toContain("Selections are review-only");
    expect(text).toContain("Selecting diagnostics does not run them.");
    expect(text).toContain("Diagnostics never apply to jobs automatically.");
    expect(text).toContain("Execution is not enabled yet. Selections are for admin review only.");
  });

  it("never renders a <details> element", () => {
    const { container } = render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    expect(container.querySelector("details")).toBeNull();
  });

  it("renders section navigation links to all five sections", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    for (const sectionId of SECTION_IDS) {
      const links = document.querySelectorAll(`a[href="#${sectionId}"]`);
      expect(links.length).toBeGreaterThan(0);
    }
  });

  it("nests related ID inputs beneath their controlling checkbox without hiding them", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    const nestedField = document.getElementById("scanWorkspaceApprovedChangePlanId");
    expect(nestedField).not.toBeNull();
    expect(nestedField).toBeVisible();
    expect(nestedField).not.toBeDisabled();
  });

  it("makes no diagnostic backend request", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    fireEvent.click(screen.getByLabelText("Live tailoring suggestions"));
    fireEvent.click(screen.getByRole("button", { name: "Clear selections" }));
    expect(fetchMock).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});

describe("AdvancedDiagnosticsDashboard — header", () => {

  it("always renders the Advanced Diagnostics title", () => {
    render(<AdvancedDiagnosticsDashboard state={HUB_STATE} />);
    expect(within(screen.getByRole("banner")).getByRole("heading", { level: 1 })).toHaveTextContent(
      "Advanced Diagnostics",
    );
  });

  it("uses the shared app-page-header contract with the icon-tile layout, badges, and description", () => {
    render(<AdvancedDiagnosticsDashboard state={HUB_STATE} />);
    const header = screen.getByRole("banner");
    expect(header).toHaveClass("advanced-diagnostics-header");
    expect(header).toHaveClass("app-page-header");
    expect(within(header).getByRole("heading", { level: 1 })).toHaveClass("app-page-header__title");
    expect(within(header).getByText("Admin only")).toHaveClass("app-page-header__badge");
    expect(within(header).getByText("Read-only")).toHaveClass("app-page-header__badge");
    expect(
      within(header).getByText(
        "Admin workflow diagnostics for saved scan contexts and scan-specific readbacks.",
      ),
    ).toHaveClass("app-page-header__description");
    // Icon-tile layout preserved via app-page-header__main--with-icon / __copy.
    expect(header.querySelector(".app-page-header__main--with-icon")).not.toBeNull();
    expect(header.querySelector(".app-page-header__copy")).not.toBeNull();
    expect(header.querySelector(".advanced-diagnostics-header-icon-tile")).not.toBeNull();
  });

  it("keeps Change scan and Back to scan outside the main header, and Run selected diagnostics disabled", () => {
    render(<AdvancedDiagnosticsDashboard state={CONTEXT_STATE} />);
    const header = screen.getByRole("banner");
    expect(within(header).queryByRole("link", { name: "Back to scan" })).not.toBeInTheDocument();
    expect(within(header).queryByRole("link", { name: "Change scan" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run selected diagnostics" })).toBeDisabled();
  });
});
