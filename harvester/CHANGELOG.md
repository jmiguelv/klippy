# Changelog

## [0.2.0](https://github.com/jmiguelv/klippy/compare/harvester-v0.1.0...harvester-v0.2.0) (2026-04-20)


### Features

* **harvester:** add --docs-only flag to harvest only clickup documents and pages ([7e387cb](https://github.com/jmiguelv/klippy/commit/7e387cbbba5ba6b661897990bcb41d3566e80729))
* **harvester:** add --force flag for full re-harvesting ([02abf26](https://github.com/jmiguelv/klippy/commit/02abf26fbecc2d66019ebc4225c85238675c5f87))
* **harvester:** capture clickup space, folder, and list names for richer context ([e8dc0a3](https://github.com/jmiguelv/klippy/commit/e8dc0a3075d6bc5fe328f77aff4293f55f8fb8ad))
* **harvester:** enable parallel harvesting and file logging ([ba8e47f](https://github.com/jmiguelv/klippy/commit/ba8e47f87b4ac7f5e2085d2fce62797a8d6528a0))
* **harvester:** enhance logging for better visibility during harvesting ([989ebc5](https://github.com/jmiguelv/klippy/commit/989ebc5ae8f0e1f5462e69e50dc814ec032ea066))
* **harvester:** harvest readme files from github repositories ([42f56be](https://github.com/jmiguelv/klippy/commit/42f56bef214648a9708a907222ece13ed2bf050e))
* **harvester:** implement clickup client and parser with v3 docs support ([e0ac7fc](https://github.com/jmiguelv/klippy/commit/e0ac7fc63903c066c6c31f96fd60766fe7bbed90))
* **harvester:** implement github client and parser with org discovery ([8957e7e](https://github.com/jmiguelv/klippy/commit/8957e7e5c38f507fe27487116e21fe09ae21f3e6))
* **harvester:** implement granular state saving and incremental clickup sync for better recovery ([25bdd8d](https://github.com/jmiguelv/klippy/commit/25bdd8db29ea722500970259b352cc5bc8714c94))
* **harvester:** implement main entry point for data harvesting ([7af4231](https://github.com/jmiguelv/klippy/commit/7af42313b5aa8011f90970eff6b5467b7915f5da))
* **harvester:** implement orchestrator for clickup and github ingestion ([b0dca8d](https://github.com/jmiguelv/klippy/commit/b0dca8d93581b4a10bf396da8eb79e103a05e029))
* **harvester:** implement recursive clickup harvesting with ignored spaces filter ([4f142da](https://github.com/jmiguelv/klippy/commit/4f142da5838f8b9b7545df29b0318ba0cba23b28))
* **harvester:** implement state management for incremental sync ([eb37a94](https://github.com/jmiguelv/klippy/commit/eb37a9485c6695a1e38e0c506dff657932acae64))
* **harvester:** improve doc discovery and github harvesting ([988039b](https://github.com/jmiguelv/klippy/commit/988039beae5434325131b41dc1a67042e2d3c655))


### Bug Fixes

* commit uv lockfiles and fix Docker PATH for uv ([eceb784](https://github.com/jmiguelv/klippy/commit/eceb7844e6977a5ac079225935c31f90f63ef69c))
* copy uv.lock to docker containers before sync ([6de8105](https://github.com/jmiguelv/klippy/commit/6de81056142f8b96e7967dc3b835c408afe15bda))
* **harvester:** add depth fallback for clickup get_pages to handle 500 errors ([d1ad43c](https://github.com/jmiguelv/klippy/commit/d1ad43cfef962d773a9efc7e7a3101abf9325e27))
* **harvester:** expand clickup doc discovery across all parent types and support nested subpages ([65ee99f](https://github.com/jmiguelv/klippy/commit/65ee99f3c0ee19c27dd39edbb803e170a44adda1))
* **harvester:** fix clickup doc discovery pagination and page flattening ([53f17b8](https://github.com/jmiguelv/klippy/commit/53f17b8506f37fa45aeb80514beae23f66243d95))
* **harvester:** gracefully handle missing clickup doc pages (404s) ([193deb7](https://github.com/jmiguelv/klippy/commit/193deb700883f81d6ea6fec5f790bfc8b0d900a2))
* **harvester:** implement deep document discovery across spaces and folders ([ee1db61](https://github.com/jmiguelv/klippy/commit/ee1db61434022b614ecb162bd44e0fe976a17b39))
* **harvester:** implement pagination for docs and improve robustness of page harvesting ([ed25e4f](https://github.com/jmiguelv/klippy/commit/ed25e4f98a189f78db266c0118bf8d37b5df9203))
* **harvester:** implement robust response parsing and defensive checks for clickup harvesting ([e252250](https://github.com/jmiguelv/klippy/commit/e252250a3c53e4a1a1d3e1dcc8efdde04703c05d))
* **harvester:** quote all string values in YAML frontmatter and update tests ([80e3cd4](https://github.com/jmiguelv/klippy/commit/80e3cd4f8128c82d1ea9a0e7febd0a040b7fc1a7))
* **harvester:** resolve 'list' object has no attribute 'get' error in clickup doc fetching ([4f651d6](https://github.com/jmiguelv/klippy/commit/4f651d668f61ee96afc65dc2cadd641e9c3bc3c2))
* **harvester:** robustly handle None values in clickup task parsing ([55242a7](https://github.com/jmiguelv/klippy/commit/55242a772666de93fff302cceb09f0e43f908513))
* **harvester:** skip docs that consistently return 500 errors ([aa33e3b](https://github.com/jmiguelv/klippy/commit/aa33e3b06663564e2f52d769c3fcd45d1b801b29))
