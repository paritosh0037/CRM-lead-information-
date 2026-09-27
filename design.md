# Design Direction

## Project: AI-Powered CRM Lead Prioritization & Next-Best-Action System

Goal of this document: give the frontend a specific, human point of view — not a generated SaaS-dashboard default. A sales rep will look at this dozens of times a day; it should feel like a tool built by someone who has sat in a sales pit, not a demo screenshot.

---

## 1. Who this is for, and what it needs to feel like

**User:** A sales rep, mid-shift, deciding who to call next. They are not admiring the UI — they're scanning it for a number and a reason to trust it.

**Design job:** Make the score and the "why" instantly legible, make the action obvious, and never let the interface feel like it's guessing. Every AI output on screen needs to visually read as *evidence*, not decoration — this is the one thing that should differentiate this from a generic admin dashboard.

**Explicitly avoid:** the "AI product" clichés — no glowing gradient orbs, no purple-to-blue sparkle accents, no chat-bubble metaphors for the recommendation. The intelligence is expressed through structured data (SHAP factors, scores, confidence), not through "AI-ness" styling. This is a sales instrument, closer in spirit to a trading terminal or an underwriting tool than a consumer AI app.

---

## 2. Visual identity

### Color
A working, slightly industrial palette — built around the idea of a **paper trail**: ink, evidence, and a single signal color for action.

| Token | Hex | Role |
|---|---|---|
| `ink-900` | `#1B1D1F` | Primary text, headers |
| `paper-50` | `#FAFAF7` | App background (warm, not stark white) |
| `paper-100` | `#F0EFEA` | Card/panel background |
| `line-200` | `#DAD8D0` | Borders, dividers |
| `signal-600` | `#2F6F4E` | Positive signal / conversion-positive factors, "Accept" |
| `flag-600` | `#B3492E` | Negative signal / conversion-negative factors, "Override" |
| `focus-500` | `#3A5CA8` | Interactive elements, links, active states — the one true "brand" color |

Score bands map to a muted three-step scale (not full traffic-light red/yellow/green, which reads as generic): `signal-600` (high), `ink-500`-tinted neutral (mid), `flag-600` (low) — used sparingly, as a small marker, never as a full-card background wash.

No gradients. No drop shadows beyond a 1px hairline border (`line-200`) — this is a data tool, not a marketing page.

### Type
Two families, clearly distinct roles:
- **Body/UI:** a workmanlike grotesk (e.g. Inter or IBM Plex Sans) — set small, tight, information-dense. This is the majority of the interface.
- **Numbers:** a tabular-figure monospace or semi-mono (e.g. IBM Plex Mono) for every score, probability, and metric — so figures align in columns and read as *measured*, not styled. This is a deliberate, functional choice (numeric alignment in ranked tables), not decoration.

No all-caps labels. No tracked-out eyebrow text above headers. Section labels are sentence case, small, and quiet (`ink-900` at reduced size, not a separate colored "label" treatment).

### Layout
Left-aligned, dense, grid-based — closer to a spreadsheet-meets-dashboard than a marketing page. Generous horizontal rhythm between columns, tight vertical rhythm within a row, because reps scan rows, not sections.

```
┌─────────────────────────────────────────────┐
│ Sidebar (nav)  │  Content                    │
│                │  ┌───────────────────────┐  │
│ Dashboard      │  │ Page header + filters │  │
│ Ranked Leads   │  └───────────────────────┘  │
│ Analytics      │  ┌───────────────────────┐  │
│                │  │ Primary data table/     │  │
│                │  │ card grid              │  │
│                │  └───────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## 3. Page-specific direction

### Dashboard
Not a hero metric wall. Lead with a single ranked shortlist ("who to work today"), with the aggregate metrics (total leads, pipeline value, average score, distribution, funnel) as a secondary strip below — the rep's first read should be *actionable leads*, not a chart.

### Ranked Leads
A dense table, not cards. Columns: rank, company, score (monospace, right-aligned), stage, recommended action (small colored text tag, not a pill button), trend (a tiny inline sparkline, not a separate chart). Sortable by score by default.

### Lead Detail
This is the page that has to earn trust. Structure top-to-bottom as an argument, not a dashboard widget grid:
1. Score + conversion probability + recommended action, together, at the top — the "verdict"
2. The SHAP factor breakdown directly beneath it as a horizontal bar list (positive factors extending right in `signal-600`, negative extending left in `flag-600`, from a shared center axis) — this is the single most important visual on the page and deserves the most craft
3. A one-paragraph plain-language explanation, written in the interface's own voice ("Scored high because...") — not chat-styled, just body text
4. Interaction timeline below that, as a simple vertical list (date, event) — a real history, not a decorative timeline component
5. Accept / Override controls fixed at the bottom or side, always visible without scrolling back up. Override opens an inline reason field, not a modal — keep the rep's context on screen.

### Analytics
Charts here should look like they came from an analyst's notebook: labeled axes, no legends floating detached from data, muted palette reserved for the metric being shown (don't recolor every chart with the full palette — one accent per chart, `focus-500` by default, `signal-600`/`flag-600` only where the chart is explicitly showing positive/negative outcomes).

---

## 4. Interaction and motion

- No entrance animations on page load, no staggered fade-ins on cards. If something animates, it's because the rep did something (accepted, overridden, sorted, expanded a row) — motion answers an action, it doesn't perform for its own sake.
- Hover states are informational (reveal the exact number behind a rounded figure, e.g. `87` → `87.4%`), not just decorative color shifts.
- Loading states show a real skeleton of the eventual layout (rows, not a centered spinner) — this is a tool people check repeatedly; make it feel fast and legible even mid-load.

---

## 5. Writing / microcopy

- Verdict language is plain and specific: "Recommend: Call" not "AI suggests you might consider calling." State the recommendation as a fact the rep can act on or reject.
- Explanations are written as reasons, not hedges: "High conversion potential because the lead requested a demo and repeatedly visited pricing." Not "It's possible this lead may be interested based on some signals."
- Override reason field placeholder: describe what to type, not a generic prompt — e.g. "Why are you choosing a different action?" not "Enter reason..."
- Empty states are instructional: an empty Ranked Leads table (before any scoring run) should say what to do next ("Run scoring to see ranked leads"), not just "No data."
- Errors state what happened and what to do, in the product's voice — never "Oops!" or an apology.

---

## 6. Accessibility / quality floor

- Full keyboard navigation through the ranked table and lead detail actions (Accept/Override reachable and operable by keyboard)
- Visible focus states using `focus-500`, consistent everywhere
- Color is never the only signal — every score band and positive/negative factor also has a text label or icon
- Responsive down to a usable tablet width at minimum; the sales-rep-on-a-laptop case is primary, mobile is secondary
- Respect `prefers-reduced-motion` for any interaction-triggered transitions
