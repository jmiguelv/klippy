# Changelog

## [0.6.0](https://github.com/jmiguelv/klippy/compare/frontend-v0.5.0...frontend-v0.6.0) (2026-04-24)


### Features

* **frontend:** URL-per-session routing, identity page, personalised hero ([5a74ac7](https://github.com/jmiguelv/klippy/commit/5a74ac70fc51b79bcace3816ebb3f0f805df1747))

## [0.5.0](https://github.com/jmiguelv/klippy/compare/frontend-v0.4.1...frontend-v0.5.0) (2026-04-24)


### Features

* **frontend:** empty state quick-starts, focus management, slider a11y ([6edbfa2](https://github.com/jmiguelv/klippy/commit/6edbfa26c5cbff35d7ac8b44e6bc4b41eb1d508b))
* **frontend:** mobile sidebar backdrop, touch targets, themed scrollbars ([b2e48f4](https://github.com/jmiguelv/klippy/commit/b2e48f4a77a5b6f370c2ede90dc8819125388195))
* **frontend:** P3 ui-review items — fonts, streaming, numbers, a11y, placeholders ([9abe03f](https://github.com/jmiguelv/klippy/commit/9abe03f3868114db2fb210dc52b1f4586bd4be27))
* **frontend:** replace [@field](https://github.com/field):value text tokens with removable filter chips ([ca9db64](https://github.com/jmiguelv/klippy/commit/ca9db641543eea9a326c85f3397be6ee443af8ca))
* **frontend:** show active filters in user message bubble ([ea605f9](https://github.com/jmiguelv/klippy/commit/ea605f910f42cf5680627e91d24de18e9107c11b))
* **frontend:** ui/ux review improvements ([79d3db2](https://github.com/jmiguelv/klippy/commit/79d3db2057c65d722d0bfd06ab65d9ef936ed887))


### Bug Fixes

* **frontend:** prevent dark mode FOUC with blocking theme script in &lt;head&gt; ([85f9bea](https://github.com/jmiguelv/klippy/commit/85f9beaf90dc8905f41c3a1c414eb4f4c156b4c0))
* **frontend:** session icon visibility in dark mode, chip overflow scroll ([de3f05d](https://github.com/jmiguelv/klippy/commit/de3f05d008254e541e746498bd8604e969fcf4ff))

## [0.4.1](https://github.com/jmiguelv/klippy/compare/frontend-v0.4.0...frontend-v0.4.1) (2026-04-24)


### Bug Fixes

* **backend,frontend:** lower default similarity threshold to prevent empty responses ([baa6dd3](https://github.com/jmiguelv/klippy/commit/baa6dd31e6008f711e82d05923242962739f9f5a))
* **backend,frontend:** restore similarity filtering and fix session history on reload ([0ae6bb8](https://github.com/jmiguelv/klippy/commit/0ae6bb88cd76e9e0612fc0a5c1dc0a0149751390))
* **frontend:** handle home page query in onMount to prevent duplicate sessions ([f9a7f98](https://github.com/jmiguelv/klippy/commit/f9a7f98a2fa74fd05dfaf3aab1c1101d9220ea86))

## [0.4.0](https://github.com/jmiguelv/klippy/compare/frontend-v0.3.0...frontend-v0.4.0) (2026-04-23)


### Features

* chat redesign ([aa89485](https://github.com/jmiguelv/klippy/commit/aa89485e32ba2f4b33783503feab687ddfb8b284))

## [0.3.0](https://github.com/jmiguelv/klippy/compare/frontend-v0.2.0...frontend-v0.3.0) (2026-04-23)


### Features

* add user-configurable top_k and similarity threshold ([d4a1e6a](https://github.com/jmiguelv/klippy/commit/d4a1e6adb588da790804afe25dc32215fee071eb))


### Bug Fixes

* **backend:** enable true async streaming and fix qdrant async client initialization ([1adfff0](https://github.com/jmiguelv/klippy/commit/1adfff03637c427beeec17265f36a8df20567b82))
* **frontend:** auto-scroll to loading message on send ([8baa65d](https://github.com/jmiguelv/klippy/commit/8baa65d4e97ad8501426d6bd9dc51d30f0c7028a))


### Performance Improvements

* **backend:** add streaming SSE endpoint and wire frontend to stream responses ([f5ed571](https://github.com/jmiguelv/klippy/commit/f5ed57110ffeb2ebff092358b650e0c6c56f85ed))
* stream responses via SSE to eliminate perceived 3m+ wait ([f6a393a](https://github.com/jmiguelv/klippy/commit/f6a393ac221b76844124a27b44744c4c7d32f408))

## [0.2.0](https://github.com/jmiguelv/klippy/compare/frontend-v0.1.0...frontend-v0.2.0) (2026-04-20)


### Features

* add [@field](https://github.com/field):value filter tokens for faceted search ([929033d](https://github.com/jmiguelv/klippy/commit/929033d5c7581310f3fc87ee251e7ab1894e30fb))
* **explore:** add per-exchange delete on user messages ([89f9459](https://github.com/jmiguelv/klippy/commit/89f9459435dbcb3d48c1123aafbe2eae98b108d9))
* **explore:** show current chat title as heading above messages ([42f6b1e](https://github.com/jmiguelv/klippy/commit/42f6b1e1eebabbf4c03a210e94d7ebc52ff2796b))
* **explore:** smooth scroll to message on send and on response ([4c0ebfd](https://github.com/jmiguelv/klippy/commit/4c0ebfd30cd687f35b75d417969133d50083c639))
* **frontend:** add faceted search with @ autocomplete and session-persisted chips ([b3c577f](https://github.com/jmiguelv/klippy/commit/b3c577fa12117a8a4392643809f4c22300636169))
* **frontend:** add favicon ([1918e06](https://github.com/jmiguelv/klippy/commit/1918e067242a6f0b30d74da3007e2947c518db16))
* **frontend:** add unit and E2E testing infrastructure ([9d26fa3](https://github.com/jmiguelv/klippy/commit/9d26fa31126fe74312049b7c8e97d65e8bd72d78))
* **frontend:** enable markdown rendering and refine visual design ([829ab00](https://github.com/jmiguelv/klippy/commit/829ab00d2d5e474f5bb9c65174892c2cdd4493a3))
* **frontend:** implement astro-based search interface ([328e5de](https://github.com/jmiguelv/klippy/commit/328e5de14d94c2f5a38a56cc69bac21830ac2db6))
* **frontend:** migrate to SvelteKit with Svelte 5 and SSG ([58c45d1](https://github.com/jmiguelv/klippy/commit/58c45d1deba90e9aa2b9ebf746c93a6def4fb71d))
* **frontend:** replace all ad-hoc icons with lucide-svelte ([bef5b8d](https://github.com/jmiguelv/klippy/commit/bef5b8dbad20b44c5754a62b4b807b7479e1fc94))
* **frontend:** replace emojis with SVG icons and add manual refresh with cache timestamp ([f2ba70d](https://github.com/jmiguelv/klippy/commit/f2ba70d454235157dc0c67ec8f901f367613e415))
* **frontend:** show offline indicator when autocomplete stats unavailable ([12d9259](https://github.com/jmiguelv/klippy/commit/12d925988f28cef176e5542e6ceb06afed3a0a76))
* **frontend:** show offline indicator when autocomplete stats unavailable ([a604677](https://github.com/jmiguelv/klippy/commit/a6046778aae82f3c1ef08a5852eb7c1bdef51831))
* **frontend:** use substring match for @ autocomplete options ([9e09eb0](https://github.com/jmiguelv/klippy/commit/9e09eb0899a04da132f2ae6d5e4f8d588d7d7ee3))
* implement session management, context tracking, and UI refinements ([af7f65e](https://github.com/jmiguelv/klippy/commit/af7f65e3c300f3785c51952eafd215db3143051f))
* include clickable sources in response and switch to faster tree_summarize mode ([130e343](https://github.com/jmiguelv/klippy/commit/130e3434f3301517bc6826eef03aa30e759fd15c))
* increase retrieval k to 20 and fix source link clickability ([634b01b](https://github.com/jmiguelv/klippy/commit/634b01bdc8d4d569a46a34e6bf04c2df9f851d1c))


### Bug Fixes

* **explore:** persist error responses and fix scroll-to-bottom ([9042f50](https://github.com/jmiguelv/klippy/commit/9042f50ba8e222e8e8d368b8a130f17654e8653a))
* **explore:** remove footer and lock body scroll on explore route ([402e31f](https://github.com/jmiguelv/klippy/commit/402e31f7d78b27ca58745da9eaf22f73580ea94c))
* **frontend:** add safety check for markdown parsing to prevent crash ([4170130](https://github.com/jmiguelv/klippy/commit/41701305b4515802f00faf77c2788fc4317f6484))
* **frontend:** await bulk stats fetch before falling back to per-field requests ([6b9a497](https://github.com/jmiguelv/klippy/commit/6b9a49714d5ee147e27749ef4fa4c0f6c57cf4ee))
* **frontend:** fix @ autocomplete not showing dropdown ([4c698ac](https://github.com/jmiguelv/klippy/commit/4c698ace8d405e58062f966deefdb51fd37c58d2))
* **frontend:** fix value autocomplete not showing in @ filter dropdown ([1daee0f](https://github.com/jmiguelv/klippy/commit/1daee0f38878bcf532b60af1556763117b787c23))
* **frontend:** import defineConfig from vitest/config to satisfy svelte-check ([76937f5](https://github.com/jmiguelv/klippy/commit/76937f5fdabce3024342ba82931fef9d6fed7c6c))
* **frontend:** improve error reporting for backend connection issues ([3cc94e1](https://github.com/jmiguelv/klippy/commit/3cc94e1c4a2455a2350cbafdf2e0dec97b740e4d))
* **frontend:** trigger value autocomplete after field selection; handle spaces in values ([894b4b6](https://github.com/jmiguelv/klippy/commit/894b4b674065f261209fa85fc1ea915d3542b58d))
* replace hardcoded API URL with env var and expand engine tests ([d1a96fa](https://github.com/jmiguelv/klippy/commit/d1a96fa06f7c752f0af90778551da493f87222b4))


### Performance Improvements

* replace 19 per-field stats requests with single batch endpoint ([f2ee8c4](https://github.com/jmiguelv/klippy/commit/f2ee8c4314345291952993ef1ecc28c33ab77b4c))
