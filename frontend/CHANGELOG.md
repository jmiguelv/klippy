# Changelog

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
* **frontend:** improve error reporting for backend connection issues ([3cc94e1](https://github.com/jmiguelv/klippy/commit/3cc94e1c4a2455a2350cbafdf2e0dec97b740e4d))
* **frontend:** trigger value autocomplete after field selection; handle spaces in values ([894b4b6](https://github.com/jmiguelv/klippy/commit/894b4b674065f261209fa85fc1ea915d3542b58d))


### Performance Improvements

* replace 19 per-field stats requests with single batch endpoint ([f2ee8c4](https://github.com/jmiguelv/klippy/commit/f2ee8c4314345291952993ef1ecc28c33ab77b4c))
