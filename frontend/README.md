# Klippy Frontend

SvelteKit (Svelte 5) search and chat interface for Klippy.

## Development

```sh
pnpm install
pnpm dev
```

Open [http://localhost:5173](http://localhost:5173).

## Environment

Create a `.env.local` file (or copy from the root `.env.example`):

```sh
PUBLIC_API_URL=http://localhost:8000
```

## Commands

| Command          | Description                |
| :--------------- | :------------------------- |
| `pnpm dev`       | Start dev server           |
| `pnpm build`     | Production build           |
| `pnpm preview`   | Preview production build   |
| `pnpm check`     | Svelte type-check          |
| `pnpm test:unit` | Run unit tests (Vitest)    |
| `pnpm test:e2e`  | Run E2E tests (Playwright) |

## Stack

- [SvelteKit](https://kit.svelte.dev/) with static adapter
- [Svelte 5](https://svelte.dev/)
- [Vitest](https://vitest.dev/) for unit tests
- [Playwright](https://playwright.dev/) for E2E tests
