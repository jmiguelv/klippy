# UI/UX Design Review: Klippy Chat Interface

**Date:** April 23, 2026
**Reviewer:** Klippy AI Agent
**Scope:** Home Page (`/`), Chats Interface (`/chats`), and Global Component Architecture.

---

## 1. Executive Summary

The recent redesign successfully transitioned Klippy from a utilitarian search tool into a refined, conversational research environment. By adopting a "quieter" interface—stripping away heavy card chrome in favor of editorial typography and subtle structural cues—the cognitive load on the user has been significantly reduced.

The integration of the **Instrumented Retrieval Pipeline** is the standout UX achievement. It transforms the opaque "waiting" period of RAG systems into a transparent, animated sequence (Parse → Search → Retrieved → Synthesise). This manages user expectations perfectly and builds trust in the system's accuracy.

While the visual hierarchy and aesthetics are strong, there are opportunities to improve accessibility, empty states, and mobile responsiveness.

**Open architectural question:** The division between the home page and the chats interface may no longer be warranted. They are functionally identical except that the home page has no history and the input is in the centre rather than the footer. **Recommendation:** consolidate them into a single `/chats` route with a conditional empty state. This removes a navigation hop, eliminates duplicated composer code, and makes deep-linking to a new chat trivial.

---

## 2. Home Page (`/`)

### Strengths

- **Immediate Focus:** The layout drives the user's attention directly to the input field. Removing the explicit "Explore" button in favor of an implicit `Enter` submission streamlines the interaction.
- **Visual Consistency:** The new unified composer (white background, 2px red top border, soft shadow) creates a strong visual link between the entry point and the main chat interface.

### Areas for Improvement

- **[P2] Placeholder value:** The current placeholder `Ask Klippy...` is clean, but a rotating set of example queries would help new users understand the system's capabilities better than a static prompt.
- **[P3] Hint inconsistency:** The home page only shows `<kbd>↵</kbd> send`. Users can already type `@field:value` syntax which gets parsed on arrival at `/chats`, but there is no hint that this is possible. Either surface the hint or suppress filter parsing until the user is in the full chat interface.
- **[P3] Feedback on submit:** Pressing Enter navigates immediately; a subtle loading state would reassure users on slower connections.

---

## 3. Chats Interface (`/chats`)

### Strengths

- **Editorial Typography:** Switching the assistant responses to `Cormorant Garamond` creates a clear, semantic distinction between the user's input (sans-serif) and the system's synthesized knowledge (serif).
- **Red Left-Rule:** Dropping the full-card background for Klippy's answers and using a 2px `var(--kings-red)` border is an elegant, lightweight way to group content.
- **Instrumented Streaming:** The pipeline (`ol.retrieval-steps`) provides brilliant real-time feedback. The use of a pulsing red dot for the active step and a teal checkmark for completed steps is visually intuitive.
- **Collapsible Settings:** Hiding the `Top K` and `Threshold` sliders behind the "Tune" button keeps the composer compact while still exposing powerful search parameters to power users.

### Areas for Improvement

- **[P1] Filter chips missing:** Filters currently appear as raw `@field:value` text in the input box. Before the redesign they were rendered as removable chips, which was significantly easier to manage. Chips should be restored.
- **[P1] Filters not shown in user bubble:** When a query is submitted with active filters, the filters are not reflected in the user's chat bubble. The context used to generate the response is invisible to the user.
- **[P1] No user bubble on new chat:** Starting a new chat session does not create an initial user bubble, breaking the conversational turn structure.
- **[P2] Empty state:** The "Start a new conversation to begin research" text is functional but stark. This is prime real estate for "Quick Start" chips (e.g., "Summarize my recent tasks") that populate the input on click.
- **[P2] Focus management:** When the user clicks "New Chat", the input box should automatically receive focus. When "Tune" is clicked, focus should move to the first slider for keyboard accessibility.
- **[P3] Action button grouping:** The feedback (Thumbs Up/Down) and Refresh buttons are well-placed but could be visually grouped to separate them from the metadata string (time / context length).
- **[P3] Fonts:** Install the fonts, from fontsource, rather than loading from Google Fonts; avoids external network request for font loading.
- **[P3] Reduce the typing speed:** The _streaming_ typing speed is too fast and the content scrolls too quickly, making it difficult to follow.
- **[P3] Number format:**: Use `toLocaleString` for the time / tokens / etc. strings.

---

## 4. Theming and Design Tokens (`app.css`)

### Strengths

- **Data-Theme Architecture:** Implementing dark mode via CSS variables on `:root[data-theme="dark"]` is robust and requires zero JavaScript logic during render, which can prevent flash of unstyled content (FOUC) if the attribute is set synchronously before first paint.
- **Color Palette:** The `var(--ink-*)` scale provides excellent contrast ratios. The use of `--canvas` vs `--surface` creates necessary depth.

### Areas for Improvement

- **[P1] FOUC risk:** Verify that `data-theme` is written to `<html>` before the browser's first paint (i.e., in a blocking `<script>` in `<head>`, not in a Svelte `onMount`). If it runs after paint, users on dark mode will see a white flash on every load.
- **[P2] Scrollbars:** Custom scrollbars matching the `ink` and `surface` tokens would complete the dark mode experience (default browser scrollbars can be glaringly bright in dark mode on some OS).
- **[P3] Focus outlines:** The application relies primarily on default browser focus rings. Explicit `:focus-visible` styles using `var(--kings-red)` or `var(--teal)` would improve keyboard navigation aesthetics.

---

## 5. Accessibility (a11y) & Mobile

### Strengths

- **ARIA Attributes:** The `aria-hidden` tags on decorative elements (like the pulsing dots and loading rails) ensure screen readers aren't cluttered with visual noise.

### Areas for Improvement

- **[P2] Slider labels:** The `Top K` and `Threshold` inputs are wrapped in `<label>` elements, but the range inputs lack explicit `id` attributes linked via `for` attributes, which can confuse some screen readers.
- **[P2] Mobile sidebar:** On screens `<768px`, the sidebar slides in from the left but there is no backdrop to obscure the main content, nor a visible "close" button inside the sidebar itself. Users must know to tap the top-left toggle to dismiss it.
- **[P2] Touch targets:** The Rename/Delete icons in the session list appear only on hover. On touch devices hover states do not exist. These should be permanently visible (at reduced opacity) on screens without hover capability (`@media (hover: none)`).

---

## Conclusion

The redesign's typography, pipeline visualization, and theming architecture are strong foundations. The highest-priority work before a production release is the P1 cluster: restoring filter chips, showing filters in user bubbles, fixing the missing user bubble on new chat, and confirming FOUC does not occur in dark mode.
