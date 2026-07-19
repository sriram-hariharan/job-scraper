import { Check, ChevronDown, Search } from "lucide-react";
import {
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

/**
 * Adapted from Origin UI Select / Dropdown patterns by Origin UI:
 * https://21st.dev/community/components/originui/select/options-with-icon
 * https://21st.dev/community/components/originui/select/status-select
 * https://21st.dev/community/components/originui/dropdown-menu/same-width-of-trigger
 *
 * ApplyLens adaptations preserve controlled operational filters, existing
 * machine values, explicit Apply/Clear ownership, and multi-value selection.
 */

const FILTER_SELECT_OPEN_EVENT = "applylens:shared-filter-select-open";

export type SharedFilterOption = {
  value: string;
  label: string;
  tone?: "ready" | "choice" | "tailor" | "later" | "strong" | "solid" | "moderate" | "weak" | "unavailable";
};

type MenuPosition = {
  left: number;
  top?: number;
  bottom?: number;
  width: number;
  maxHeight: number;
  placement: "top" | "bottom";
};

export type SharedFilterSelectProps = {
  id: string;
  label: string;
  options: SharedFilterOption[];
  values: string[];
  onChange: (values: string[]) => void;
  placeholder: string;
  allLabel?: string;
  mode: "single" | "multiple";
  searchable?: boolean;
  disabled?: boolean;
};

function normalizeSearchText(value: string): string {
  return value.toLowerCase().replace(/[\/_-]+/g, " ").trim().replace(/\s+/g, " ");
}

export function SharedFilterSelect({
  id,
  label,
  options,
  values,
  onChange,
  placeholder,
  allLabel,
  mode,
  searchable = false,
  disabled = false,
}: SharedFilterSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [position, setPosition] = useState<MenuPosition | null>(null);
  const instanceId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const labelId = `${id}-label`;
  const menuId = `${id}-menu`;

  const normalizedQuery = normalizeSearchText(query);
  const visibleOptions = useMemo(
    () => options.filter((option) => normalizeSearchText(option.label).includes(normalizedQuery)),
    [normalizedQuery, options],
  );
  const allOptionVisible = Boolean(allLabel && (!normalizedQuery || normalizeSearchText(allLabel).includes(normalizedQuery)));
  const menuOptions = useMemo(
    () => [
      ...(allOptionVisible ? [{ value: "__all__", label: allLabel || placeholder, isAll: true }] : []),
      ...visibleOptions.map((option) => ({ ...option, isAll: false })),
    ],
    [allLabel, allOptionVisible, placeholder, visibleOptions],
  );
  const selectedLabels = values.map((value) => options.find((option) => option.value === value)?.label).filter(Boolean);
  const triggerLabel = selectedLabels.length === 0
    ? placeholder
    : selectedLabels.length === 1
      ? selectedLabels[0]
      : `${selectedLabels.length} selected`;

  const updatePosition = () => {
    const trigger = triggerRef.current;
    if (!trigger) return;
    const rect = trigger.getBoundingClientRect();
    const viewportPadding = 12;
    const availableWidth = Math.max(220, window.innerWidth - viewportPadding * 2);
    const width = Math.min(Math.max(rect.width, 240), availableWidth);
    const left = Math.min(Math.max(rect.left, viewportPadding), window.innerWidth - width - viewportPadding);
    const below = window.innerHeight - rect.bottom - viewportPadding;
    const above = rect.top - viewportPadding;
    const placement = below < 190 && above > below ? "top" : "bottom";
    const availableHeight = placement === "top" ? above : below;
    const maxHeight = Math.max(150, Math.min(320, availableHeight - 8));
    setPosition({
      left,
      width,
      maxHeight,
      placement,
      ...(placement === "top"
        ? { bottom: window.innerHeight - rect.top + 6 }
        : { top: rect.bottom + 6 }),
    });
  };

  const close = (returnFocus = false) => {
    setOpen(false);
    setQuery("");
    setActiveIndex(0);
    if (returnFocus) window.requestAnimationFrame(() => triggerRef.current?.focus());
  };

  const openMenu = () => {
    if (disabled) return;
    window.dispatchEvent(new CustomEvent(FILTER_SELECT_OPEN_EVENT, { detail: { instanceId } }));
    setOpen(true);
    setActiveIndex(0);
  };

  useLayoutEffect(() => {
    if (open) updatePosition();
  }, [open, menuOptions.length]);

  useEffect(() => {
    if (!open) return undefined;
    const handleOtherOpen = (event: Event) => {
      if ((event as CustomEvent<{ instanceId?: string }>).detail?.instanceId !== instanceId) close(false);
    };
    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (!triggerRef.current?.contains(target) && !menuRef.current?.contains(target)) close(false);
    };
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close(true);
      }
    };
    const handleViewportChange = () => updatePosition();
    window.addEventListener(FILTER_SELECT_OPEN_EVENT, handleOtherOpen);
    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    window.addEventListener("resize", handleViewportChange);
    window.addEventListener("scroll", handleViewportChange, true);
    return () => {
      window.removeEventListener(FILTER_SELECT_OPEN_EVENT, handleOtherOpen);
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
      window.removeEventListener("resize", handleViewportChange);
      window.removeEventListener("scroll", handleViewportChange, true);
    };
  }, [instanceId, open]);

  useEffect(() => {
    if (!open || searchable) return;
    window.requestAnimationFrame(() => optionRefs.current[activeIndex]?.focus());
  }, [activeIndex, open, searchable]);

  const selectOption = (value: string, isAll: boolean) => {
    if (isAll) {
      onChange([]);
    } else if (mode === "single") {
      onChange([value]);
    } else {
      onChange(values.includes(value) ? values.filter((candidate) => candidate !== value) : [...values, value]);
    }
    if (mode === "single") close(true);
  };

  const moveActive = (next: number) => {
    if (!menuOptions.length) return;
    const bounded = (next + menuOptions.length) % menuOptions.length;
    setActiveIndex(bounded);
    window.requestAnimationFrame(() => optionRefs.current[bounded]?.focus());
  };

  const handleOptionKeyDown = (event: ReactKeyboardEvent<HTMLButtonElement>, index: number) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      const option = menuOptions[index];
      if (option) selectOption(option.value, option.isAll);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActive(index + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(index - 1);
    } else if (event.key === "Home") {
      event.preventDefault();
      moveActive(0);
    } else if (event.key === "End") {
      event.preventDefault();
      moveActive(menuOptions.length - 1);
    } else if (event.key === "Tab") {
      close(false);
    }
  };

  const menuStyle = position ? ({
    left: position.left,
    top: position.top,
    bottom: position.bottom,
    width: position.width,
    maxHeight: position.maxHeight,
  } satisfies CSSProperties) : undefined;

  const menu = open && position ? createPortal(
    <div
      className="shared-filter-select__menu"
      id={menuId}
      ref={menuRef}
      role="listbox"
      aria-labelledby={labelId}
      aria-multiselectable={mode === "multiple"}
      data-placement={position.placement}
      style={menuStyle}
    >
      {searchable ? (
        <label className="shared-filter-select__search">
          <span className="sr-only">Search {label.toLowerCase()}</span>
          <Search size={15} aria-hidden="true" />
          <input
            autoFocus
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown" && menuOptions.length) {
                event.preventDefault();
                optionRefs.current[0]?.focus();
              } else if (event.key === "Tab") {
                close(false);
              }
            }}
            placeholder={`Search ${label.toLowerCase()}`}
          />
        </label>
      ) : null}
      <div className="shared-filter-select__options">
        {menuOptions.map((option, index) => {
          const selected = option.isAll ? values.length === 0 : values.includes(option.value);
          return (
            <button
              type="button"
              className={`shared-filter-select__option ${selected ? "is-selected" : ""} ${"tone" in option && option.tone ? "has-tone" : ""}`}
              key={option.value}
              ref={(node) => { optionRefs.current[index] = node; }}
              role="option"
              aria-selected={selected}
              tabIndex={index === activeIndex ? 0 : -1}
              onFocus={() => setActiveIndex(index)}
              onKeyDown={(event) => handleOptionKeyDown(event, index)}
              onClick={() => selectOption(option.value, option.isAll)}
            >
              <Check className="shared-filter-select__check" size={15} aria-hidden="true" />
              {"tone" in option && option.tone ? (
                <span className={`shared-filter-select__dot shared-filter-select__dot--${option.tone}`} aria-hidden="true" />
              ) : null}
              <span>{option.label}</span>
            </button>
          );
        })}
        {!menuOptions.length ? <div className="shared-filter-select__empty">No options found</div> : null}
      </div>
    </div>,
    document.body,
  ) : null;

  return (
    <div className="shared-filter-select" data-filter-select-id={id}>
      <span className="shared-filter-select__label" id={labelId}>{label}</span>
      <button
        type="button"
        className="shared-filter-select__trigger"
        id={id}
        ref={triggerRef}
        aria-labelledby={`${labelId} ${id}-value`}
        aria-haspopup="listbox"
        aria-controls={menuId}
        aria-expanded={open}
        disabled={disabled}
        onClick={() => open ? close(false) : openMenu()}
        onKeyDown={(event) => {
          if (["Enter", " ", "ArrowDown", "ArrowUp"].includes(event.key)) {
            event.preventDefault();
            if (!open) openMenu();
          }
        }}
      >
        <span id={`${id}-value`} title={triggerLabel}>{triggerLabel}</span>
        <ChevronDown size={15} aria-hidden="true" />
      </button>
      {menu}
    </div>
  );
}
