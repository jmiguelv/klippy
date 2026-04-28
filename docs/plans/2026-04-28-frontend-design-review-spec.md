# Design Spec: Frontend Inconsistency Fixes & Architectural Consolidation

**Date:** 2026-04-28
**Status:** Approved
**Scope:** Frontend (SvelteKit)

---

## 1. Goal
The primary objective is to resolve design and architectural inconsistencies across the Klippy frontend. This includes consolidating fragmented routes, eliminating code duplication in the query interface, and refining the "last mile" UX details (theming, z-index, mobile responsiveness).

## 2. Architecture & Route Consolidation

### 2.1 Unified Root (`/`)
- **Change:** Merge the identity/home page logic into the root route.
- **Behavior:**
  - If `localStorage.getItem('klippy_user_name')` is empty, render the `IdentityForm` component.
  - If a user name exists, render the `ChatHero` (currently in `/chats`).
  - Eliminate the redirect from `/` to `/chats`.
- **Structural Continuity:** Maintain the application layout (navigation bar and sidebar structure) during the identity phase, potentially with a de-emphasized or empty sidebar, to avoid jarring transitions.

### 2.2 Route Cleanup
- **Remove:** `/chats/+page.svelte` (logic moved to root).
- **Update:** Deep links to chat instances (`/chats/[id]`) will remain but will trigger the global identity gate if no user name is set.

## 3. Componentization: The Unified Composer

### 3.1 `Composer.svelte`
- **Purpose:** A single, smart component responsible for all user input.
- **Features:**
  - Integrated filter parsing (`@field:value`) and chip rendering.
  - Collapsible search settings (Top K, Threshold).
  - Persistence of settings (Top K/Threshold) in the global `chatState`.
  - Reusable across the Chat Hero (root) and individual chat sessions.

### 3.2 Autocomplete Extraction
- **Action/Helper:** Extract the autocomplete logic (regex matching for fields/values, stats fetching) into a Svelte Action (`useAutocomplete.ts`) or a standalone utility.
- **Consistency:** Ensure the identity form (name selection) and the composer (filter selection) use the same underlying logic and UI component for dropdowns.

## 4. UI/UX Refinement & Polish

### 4.1 FOUC Prevention (Dark Mode)
- **Change:** Move theme detection from Svelte's `onMount` to a blocking `<script>` in the `<head>` of `app.html`.
- **Implementation:** Check `localStorage` and apply `data-theme` to `document.documentElement` immediately to prevent the white flash on load.

### 4.2 Z-Index Management
- **Centralization:** Define semantic z-index variables in `app.css`:
  - `--z-hide: -1;`
  - `--z-base: 1;`
  - `--z-nav: 100;`
  - `--z-sidebar: 200;`
  - `--z-dropdown: 300;`
  - `--z-modal: 400;`
  - `--z-toast: 500;`

### 4.3 Mobile Navigation
- **Sidebar Polish:**
  - Add a dimmed backdrop when the sidebar is open on mobile (`< 768px`).
  - Add an explicit "Close" button within the sidebar for mobile users.
  - Ensure touch targets for session management (rename/delete) are visible on mobile.

## 5. Technical Requirements
- **State Management:** Use the existing `$state` and `$derived` runes (Svelte 5) consistently.
- **Styles:** Use Vanilla CSS with established tokens in `app.css`.
- **Testing:** Add/update unit tests for filter parsing and autocomplete matching.

## 6. Verification Plan
- **Manual Verification:**
  - Verify theme persistence and flash prevention across reloads.
  - Test the identity-to-hero flow on the root route.
  - Validate filter chip behavior and search settings persistence.
- **Automated Tests:**
  - `pnpm test` for logic verification.
  - `pnpm playwright test` for mobile layout and sidebar regression.
