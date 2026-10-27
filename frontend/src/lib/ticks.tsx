import React from "react";

/**
 * The audit engine marks IDs and versions with Markdown backticks
 * (e.g. "`PS-109`", "`v2026_draft`"). Render those as small ID chips
 * instead of showing the backtick characters.
 */
export function ticks(text: string | null | undefined): React.ReactNode {
  if (!text) return text ?? null;
  if (!text.includes("`")) return text;
  return text.split(/(`[^`]+`)/g).map((part, i) =>
    part.length > 2 && part.startsWith("`") && part.endsWith("`") ? (
      <span
        key={i}
        className="whitespace-nowrap rounded bg-ink-950/[0.06] px-1 py-px font-mono text-[0.92em] text-ink-900"
      >
        {part.slice(1, -1)}
      </span>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}
