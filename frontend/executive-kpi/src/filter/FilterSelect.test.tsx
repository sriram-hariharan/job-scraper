import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { useState } from "react";
import { SharedFilterSelect, type SharedFilterOption } from "./FilterSelect";

const OPTIONS: SharedFilterOption[] = [
  { value: "APPLY", label: "Ready for review", tone: "ready" },
  { value: "MAYBE_TAILOR", label: "Tailor first", tone: "tailor" },
  { value: "DATA_ENGINEERING", label: "Data Engineering" },
];

function ControlledSelect({
  id = "testFilter",
  searchable = true,
  disabled = false,
  mode = "single",
  portalClassName,
}: {
  id?: string;
  searchable?: boolean;
  disabled?: boolean;
  mode?: "single" | "multiple";
  portalClassName?: string;
}) {
  const [values, setValues] = useState<string[]>([]);
  return (
    <SharedFilterSelect
      id={id}
      label="Action"
      options={OPTIONS}
      values={values}
      onChange={setValues}
      placeholder="All actions"
      allLabel="All actions"
      searchable={searchable}
      disabled={disabled}
      mode={mode}
      portalClassName={portalClassName}
    />
  );
}

beforeEach(() => {
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
    x: 100,
    y: 120,
    top: 120,
    left: 100,
    right: 320,
    bottom: 160,
    width: 220,
    height: 40,
    toJSON: () => ({}),
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("renders an associated controlled trigger and selected checkmark", () => {
  render(<ControlledSelect />);
  const trigger = screen.getByRole("button", { name: "Action All actions" });
  expect(trigger).toHaveAttribute("aria-expanded", "false");
  fireEvent.click(trigger);
  const selectedAll = screen.getByRole("option", { name: "All actions" });
  expect(selectedAll).toHaveAttribute("aria-selected", "true");
  expect(selectedAll.querySelector(".shared-filter-select__check")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("option", { name: "Ready for review" }));
  expect(screen.getByRole("button", { name: "Action Ready for review" })).toHaveAttribute("aria-expanded", "false");
});

it("normalizes searchable text and keeps the menu viewport-bounded", () => {
  render(<ControlledSelect />);
  fireEvent.click(screen.getByRole("button", { name: "Action All actions" }));
  const menu = screen.getByRole("listbox");
  const search = screen.getByRole("searchbox");
  expect(document.body).toContainElement(menu);
  expect(menu).toHaveStyle({ left: "100px", width: "240px" });
  expect(search).toHaveClass("shared-filter-select__search-input");
  expect(search.closest(".shared-filter-select__search")).not.toBeNull();
  expect(search).not.toHaveClass("form-control");
  expect(search.closest(".shared-filter-select__search")?.querySelector("svg")).toHaveAttribute("width", "17");
  fireEvent.change(search, { target: { value: "data-eng" } });
  expect(screen.getByRole("option", { name: "Data Engineering" })).toBeInTheDocument();
  expect(screen.queryByRole("option", { name: "Ready for review" })).not.toBeInTheDocument();
});

it("moves keyboard focus from the integrated search row into options", async () => {
  render(<ControlledSelect />);
  fireEvent.click(screen.getByRole("button", { name: "Action All actions" }));
  const search = screen.getByRole("searchbox");
  await waitFor(() => expect(search).toHaveFocus());
  fireEvent.keyDown(search, { key: "ArrowDown" });
  await waitFor(() => expect(screen.getByRole("option", { name: "All actions" })).toHaveFocus());
});

it("leaves non-searchable menus without search-header markup", () => {
  render(<ControlledSelect searchable={false} />);
  fireEvent.click(screen.getByRole("button", { name: "Action All actions" }));
  expect(screen.queryByRole("searchbox")).not.toBeInTheDocument();
  expect(screen.getByRole("listbox")).toHaveAttribute("data-searchable", "false");
  expect(screen.getAllByRole("option")).toHaveLength(4);
});

it("never positions a minimum-width menu beyond a narrow viewport", () => {
  vi.stubGlobal("innerWidth", 200);
  render(<ControlledSelect />);
  fireEvent.click(screen.getByRole("button", { name: "Action All actions" }));
  expect(screen.getByRole("listbox")).toHaveStyle({ left: "12px", width: "176px" });
});

it("applies an optional portalClassName to the portaled menu without changing default behavior", () => {
  render(<ControlledSelect portalClassName="advanced-diagnostics-scan-menu" />);
  fireEvent.click(screen.getByRole("button", { name: "Action All actions" }));
  const menu = screen.getByRole("listbox");
  expect(menu).toHaveClass("shared-filter-select__menu");
  expect(menu).toHaveClass("advanced-diagnostics-scan-menu");
});

it("omits the portal class entirely when a caller does not supply portalClassName", () => {
  render(<ControlledSelect />);
  fireEvent.click(screen.getByRole("button", { name: "Action All actions" }));
  const menu = screen.getByRole("listbox");
  expect(menu).toHaveClass("shared-filter-select__menu");
  expect(menu.className.trim()).toBe("shared-filter-select__menu");
});

it("supports keyboard navigation, Escape, outside close, and one open menu", async () => {
  render(<><ControlledSelect id="firstFilter" searchable={false} /><ControlledSelect id="secondFilter" searchable={false} /></>);
  const [first, second] = screen.getAllByRole("button", { name: "Action All actions" });
  fireEvent.keyDown(first, { key: "Enter" });
  expect(first).toHaveAttribute("aria-expanded", "true");
  fireEvent.keyDown(screen.getByRole("option", { name: "All actions" }), { key: "ArrowDown" });
  fireEvent.keyDown(screen.getByRole("option", { name: "Ready for review" }), { key: "Enter" });
  await waitFor(() => expect(first).toHaveFocus());

  fireEvent.click(first);
  fireEvent.keyDown(document, { key: "Escape" });
  expect(first).toHaveAttribute("aria-expanded", "false");
  await waitFor(() => expect(first).toHaveFocus());

  fireEvent.click(first);
  fireEvent.click(second);
  expect(first).toHaveAttribute("aria-expanded", "false");
  expect(second).toHaveAttribute("aria-expanded", "true");
  fireEvent.pointerDown(document.body);
  expect(second).toHaveAttribute("aria-expanded", "false");
});

it("respects disabled state", () => {
  render(<ControlledSelect disabled />);
  const trigger = screen.getByRole("button", { name: "Action All actions" });
  expect(trigger).toBeDisabled();
  fireEvent.click(trigger);
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});

it("keeps multiple selection open while toggling preferences and summarizes the count", () => {
  render(<ControlledSelect mode="multiple" />);
  fireEvent.click(screen.getByRole("button", { name: "Action All actions" }));
  fireEvent.click(screen.getByRole("option", { name: "Ready for review" }));
  expect(screen.getByRole("listbox")).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "Ready for review" })).toHaveAttribute("aria-selected", "true");
  fireEvent.click(screen.getByRole("option", { name: "Tailor first" }));
  expect(screen.getByRole("button", { name: "Action 2 selected" })).toHaveAttribute("aria-expanded", "true");
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "ready" } });
  expect(screen.getByRole("option", { name: "Ready for review" })).toHaveAttribute("aria-selected", "true");
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "" } });
  fireEvent.click(screen.getByRole("option", { name: "Ready for review" }));
  expect(screen.getByRole("button", { name: "Action Tailor first" })).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByRole("option", { name: "Tailor first" })).toHaveAttribute("aria-selected", "true");
  fireEvent.click(screen.getByRole("option", { name: "All actions" }));
  expect(screen.getByRole("button", { name: "Action All actions" })).toHaveAttribute("aria-expanded", "true");
});

it("exposes shared open/searchable state hooks and a compact empty search row", () => {
  const { container } = render(<ControlledSelect />);
  const root = container.querySelector(".shared-filter-select");
  const trigger = screen.getByRole("button", { name: "Action All actions" });

  expect(root).toHaveAttribute("data-state", "closed");
  expect(root).toHaveAttribute("data-searchable", "true");
  fireEvent.click(trigger);
  expect(root).toHaveClass("is-open");
  expect(root).toHaveAttribute("data-state", "open");
  expect(trigger).toHaveClass("is-open");
  expect(screen.getByRole("listbox")).toHaveAttribute("data-searchable", "true");
  expect(screen.getByRole("option", { name: "All actions" })).toHaveClass("is-all", "is-selected");
  expect(screen.getByRole("option", { name: "Ready for review" }).querySelector(".shared-filter-select__dot--ready")).toBeInTheDocument();

  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "no-match-here" } });
  expect(screen.queryAllByRole("option")).toHaveLength(0);
  expect(screen.getByText("No options found")).toHaveClass("shared-filter-select__empty");
});

it("supports Arrow, Home, End, Space, and Tab without changing selection semantics", async () => {
  render(<ControlledSelect searchable={false} />);
  const trigger = screen.getByRole("button", { name: "Action All actions" });

  fireEvent.keyDown(trigger, { key: "ArrowDown" });
  const options = screen.getAllByRole("option");
  const lastOption = options[options.length - 1];
  await waitFor(() => expect(options[0]).toHaveFocus());
  fireEvent.keyDown(options[0], { key: "End" });
  await waitFor(() => expect(lastOption).toHaveFocus());
  fireEvent.keyDown(lastOption, { key: "Home" });
  await waitFor(() => expect(options[0]).toHaveFocus());
  fireEvent.keyDown(options[0], { key: "ArrowUp" });
  await waitFor(() => expect(lastOption).toHaveFocus());
  fireEvent.keyDown(lastOption, { key: " " });
  await waitFor(() => expect(trigger).toHaveFocus());
  expect(trigger).toHaveAttribute("aria-expanded", "false");

  fireEvent.click(trigger);
  const firstOption = screen.getAllByRole("option")[0];
  fireEvent.keyDown(firstOption, { key: "Tab" });
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});

it("preserves viewport-aware top placement and bounded portal sizing", () => {
  vi.stubGlobal("innerHeight", 800);
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
    x: 100,
    y: 740,
    top: 740,
    left: 100,
    right: 320,
    bottom: 780,
    width: 220,
    height: 40,
    toJSON: () => ({}),
  });

  render(<ControlledSelect searchable={false} />);
  fireEvent.click(screen.getByRole("button", { name: "Action All actions" }));
  const menu = screen.getByRole("listbox");
  expect(document.body).toContainElement(menu);
  expect(menu).toHaveAttribute("data-placement", "top");
  expect(menu).toHaveStyle({ left: "100px", bottom: "66px", width: "240px", maxHeight: "320px" });
});
