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
}: {
  id?: string;
  searchable?: boolean;
  disabled?: boolean;
  mode?: "single" | "multiple";
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

afterEach(() => vi.restoreAllMocks());

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
  expect(document.body).toContainElement(menu);
  expect(menu).toHaveStyle({ left: "100px", width: "240px" });
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "data-eng" } });
  expect(screen.getByRole("option", { name: "Data Engineering" })).toBeInTheDocument();
  expect(screen.queryByRole("option", { name: "Ready for review" })).not.toBeInTheDocument();
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
