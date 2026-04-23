# Changelog

## [0.4.0](https://github.com/jmiguelv/klippy/compare/backend-v0.3.1...backend-v0.4.0) (2026-04-23)


### Features

* add user-configurable top_k and similarity threshold ([d4a1e6a](https://github.com/jmiguelv/klippy/commit/d4a1e6adb588da790804afe25dc32215fee071eb))
* **backend:** add LLM_CONTEXT_WINDOW environment variable ([2819d2d](https://github.com/jmiguelv/klippy/commit/2819d2d7691c0d811eff20bec71268ca36d70072))


### Bug Fixes

* **backend:** enable true async streaming and fix qdrant async client initialization ([1adfff0](https://github.com/jmiguelv/klippy/commit/1adfff03637c427beeec17265f36a8df20567b82))
* **backend:** restore chat history continuity and fix serialization ([bb081f5](https://github.com/jmiguelv/klippy/commit/bb081f55d894052f7c9ae5aff7f2d4ba78d7b124))


### Performance Improvements

* **backend:** add streaming SSE endpoint and wire frontend to stream responses ([f5ed571](https://github.com/jmiguelv/klippy/commit/f5ed57110ffeb2ebff092358b650e0c6c56f85ed))
* stream responses via SSE to eliminate perceived 3m+ wait ([f6a393a](https://github.com/jmiguelv/klippy/commit/f6a393ac221b76844124a27b44744c4c7d32f408))

## [0.3.1](https://github.com/jmiguelv/klippy/compare/backend-v0.3.0...backend-v0.3.1) (2026-04-22)


### Bug Fixes

* **backend:** restore conversation continuity broken by engine-history refactor ([82d44e7](https://github.com/jmiguelv/klippy/commit/82d44e790877a7511cdb77677a3d18b450a0a4ca))
* **backend:** restore explicit chat history construction to fix conversation continuity ([9730fd0](https://github.com/jmiguelv/klippy/commit/9730fd033449b25629c7339f4c8c2ace0e5980ef))
* **backend:** serialize chat history via m.content instead of m.dict() ([dfce804](https://github.com/jmiguelv/klippy/commit/dfce8045c670553b829fb20b15d723407a8313a7))


### Performance Improvements

* **backend:** increase similarity_top_k from 10 to 20 for larger context window ([7c4b85f](https://github.com/jmiguelv/klippy/commit/7c4b85fac2f8e992ed705aa210bd713227360cd2))

## [0.3.0](https://github.com/jmiguelv/klippy/compare/backend-v0.2.0...backend-v0.3.0) (2026-04-22)


### Features

* **backend:** switch to jinaai/jina-embeddings-v5-text-small ([cb47653](https://github.com/jmiguelv/klippy/commit/cb47653bdb333b78bb13c3acbeb1995b9facdb07))
* **backend:** switch to jinaai/jina-embeddings-v5-text-small ([e927177](https://github.com/jmiguelv/klippy/commit/e92717763c71b4187671290d259ba66c4efe18fa))


### Bug Fixes

* **backend:** add peft dependency required by jina-embeddings-v5 ([4aa20e1](https://github.com/jmiguelv/klippy/commit/4aa20e14a4d3dc46cd22537ff1cd31c3a488077d))
* **backend:** autodetect torch device when EMBED_DEVICE not set ([54d9b74](https://github.com/jmiguelv/klippy/commit/54d9b749fa5a3cd9bb971b29e8dcb3b328ea13c6))
* **backend:** improve embed device logging to show source of selection ([b83e45c](https://github.com/jmiguelv/klippy/commit/b83e45cc94f56a267c0d8f35cc7d814cc2ab86c4))
* **backend:** pass default_task=retrieval to jina-embeddings-v5 ([f71cd7a](https://github.com/jmiguelv/klippy/commit/f71cd7a73a556100113c01932b06fada93282fbd))
* **backend:** pin dense_vector_name to text-dense in QdrantVectorStore ([ba9f088](https://github.com/jmiguelv/klippy/commit/ba9f08832c75457ebb09bd7a3fac9783bbe3a7a1))
* **backend:** prevent empty EMBED_MODEL/EMBED_DEVICE from compose overriding defaults ([deca64c](https://github.com/jmiguelv/klippy/commit/deca64cbc01a01b0adaed6d15c775718096d93f0))

## [0.2.0](https://github.com/jmiguelv/klippy/compare/backend-v0.1.0...backend-v0.2.0) (2026-04-20)


### Features

* add [@field](https://github.com/field):value filter tokens for faceted search ([929033d](https://github.com/jmiguelv/klippy/commit/929033d5c7581310f3fc87ee251e7ab1894e30fb))
* **backend:** add CLI support for running ingestion via --ingest flag ([55fb158](https://github.com/jmiguelv/klippy/commit/55fb158d85906114f38e049d28b272fdb3347a09))
* **backend:** add feedback endpoint to handle cache clearing on thumbs down ([b9ebee2](https://github.com/jmiguelv/klippy/commit/b9ebee2a2c2fc4474a4f97bd555b86f91db0df68))
* **backend:** enable ingestion caching using Redis to avoid re-processing unchanged files ([94090ce](https://github.com/jmiguelv/klippy/commit/94090ce8dfd020caa9e9d623ade57b71113040ef))
* **backend:** extract YAML frontmatter during ingestion for metadata filtering ([5251f30](https://github.com/jmiguelv/klippy/commit/5251f3018730b8303d58efa0abfeb9d6c5fd679e))
* **backend:** implement fastapi RAG engine with llamaindex and qdrant ([68f0f0a](https://github.com/jmiguelv/klippy/commit/68f0f0ab4f77338ee0b2df5ebbdf7f51f2014e0d))
* **backend:** implement strict system prompt to ensure context-only answers ([7fd6d4b](https://github.com/jmiguelv/klippy/commit/7fd6d4bba3bd703915240190b8675b5e9a5aad96))
* **backend:** load system prompt from data/final/prompt.md ([ad1508a](https://github.com/jmiguelv/klippy/commit/ad1508a0afd09c4f839eb9209815836490a9ae10))
* **backend:** support force re-indexing and YAML metadata extraction ([0041cb0](https://github.com/jmiguelv/klippy/commit/0041cb0f75e1d5452bc4a5da36ff11e8c4dbc1f0))
* **backend:** support hardware acceleration for embeddings via EMBED_DEVICE ([d5aa79e](https://github.com/jmiguelv/klippy/commit/d5aa79ece7a01f29f28d75006e4a4bc217af393b))
* **backend:** support limited random ingestion and make processes manual ([1a38e74](https://github.com/jmiguelv/klippy/commit/1a38e746839718baf7ee3a3f97d9a1b6af7dd741))
* **backend:** support local HuggingFace embedding models ([06527d7](https://github.com/jmiguelv/klippy/commit/06527d773ad434e56b6e72114be06084a8159183))
* **backend:** support openai-compatible endpoints with LLM_BASE_URL ([f2c532b](https://github.com/jmiguelv/klippy/commit/f2c532b90b50f474501c1839bf428d012124efa4))
* **backend:** support specifying LLM and EMBED models in environment ([8a94e2b](https://github.com/jmiguelv/klippy/commit/8a94e2bba84eda568edca37bfeafaf4d06cf6169))
* **frontend:** add faceted search with @ autocomplete and session-persisted chips ([b3c577f](https://github.com/jmiguelv/klippy/commit/b3c577fa12117a8a4392643809f4c22300636169))
* **frontend:** migrate to SvelteKit with Svelte 5 and SSG ([58c45d1](https://github.com/jmiguelv/klippy/commit/58c45d1deba90e9aa2b9ebf746c93a6def4fb71d))
* implement session management, context tracking, and UI refinements ([af7f65e](https://github.com/jmiguelv/klippy/commit/af7f65e3c300f3785c51952eafd215db3143051f))
* include clickable sources in response and switch to faster tree_summarize mode ([130e343](https://github.com/jmiguelv/klippy/commit/130e3434f3301517bc6826eef03aa30e759fd15c))
* increase retrieval k to 20 and fix source link clickability ([634b01b](https://github.com/jmiguelv/klippy/commit/634b01bdc8d4d569a46a34e6bf04c2df9f851d1c))


### Bug Fixes

* **backend:** add CORS middleware to allow frontend communication ([558c8d9](https://github.com/jmiguelv/klippy/commit/558c8d9047c6f79353363013262cba794590fd5a))
* **backend:** add llama-index-readers-file dependency ([98e430f](https://github.com/jmiguelv/klippy/commit/98e430f0753cd9257988f1738c68e824b5a295c8))
* **backend:** add missing json import for redis caching ([4635fc6](https://github.com/jmiguelv/klippy/commit/4635fc635ec1344bd968bed8916743d88acc53c5))
* **backend:** allow startup even if data directory is empty ([77cbe0c](https://github.com/jmiguelv/klippy/commit/77cbe0c81822001c494aa8df258d94ffba2586ba))
* **backend:** apply strict prompt to both text_qa and refine templates to prevent gpt-3.5-turbo default ([cc1b781](https://github.com/jmiguelv/klippy/commit/cc1b7811bf86b8a9877e658f4fa00e403764aa13))
* **backend:** clear collection before force re-index ([ca7f918](https://github.com/jmiguelv/klippy/commit/ca7f9187884260f7ac9098f42bb65c661d048758))
* **backend:** correct indentation error in engine.py ([bbfe53d](https://github.com/jmiguelv/klippy/commit/bbfe53d2f65504fe50e18ccfa3f2258456f5d223))
* **backend:** explicitly pass LLM to query engine to avoid gpt-3.5-turbo default ([c6ebd9a](https://github.com/jmiguelv/klippy/commit/c6ebd9af7e2727e53cae4de39f7044e4e2b1d383))
* **backend:** explicitly pass LLM to response synthesizer to prevent gpt-3.5-turbo default ([e7c1fc7](https://github.com/jmiguelv/klippy/commit/e7c1fc79a3fed06697de47b7b0e5e7e4e8b1baad))
* **backend:** fix phoenix tracing endpoint and add embedding model warning ([f54f9a6](https://github.com/jmiguelv/klippy/commit/f54f9a665405d1c84dbf68c5c48f25dd11d34804))
* **backend:** generate deterministic UUIDs for Qdrant compatibility ([5175dc7](https://github.com/jmiguelv/klippy/commit/5175dc7a16f1956c959cbcbc7f8deff726cd3cfe))
* **backend:** improve ingestion pipeline and clean up code ([37fe094](https://github.com/jmiguelv/klippy/commit/37fe094a044f243b5d4bcd22ce891a305247e5b2))
* **backend:** install arize-phoenix for observability ([2d87cf9](https://github.com/jmiguelv/klippy/commit/2d87cf9bdd1d0b129e09c3e5627e28ddfdeffa5d))
* **backend:** install both arize-phoenix and llama-index callbacks ([3b27933](https://github.com/jmiguelv/klippy/commit/3b27933200a4b85a06295d0d3c3db078b4c2280c))
* **backend:** restore conversation context between requests ([5bd7bc5](https://github.com/jmiguelv/klippy/commit/5bd7bc59deeb304ed2f4dba9276fd4eaea80f7e0))
* **backend:** run initial ingestion in background to avoid blocking server startup ([43d1f59](https://github.com/jmiguelv/klippy/commit/43d1f59e2cd0352ad8dc32a651ce232ec3b33e42))
* **backend:** use aggressive explicit LLM configuration to prevent gpt-3.5-turbo fallback ([962086d](https://github.com/jmiguelv/klippy/commit/962086deead704192b1b657f53788cca989c0b2c))
* **backend:** use context_prompt parameter for condense_plus_context chat mode to fix follow-up issues ([75c1133](https://github.com/jmiguelv/klippy/commit/75c1133284b9c844001f2f6ba2c60c856b00c908))
* **backend:** use correct chat_history attribute and robust deserialization for conversational memory ([e30f436](https://github.com/jmiguelv/klippy/commit/e30f4361ace5d81dbb55cc5ba3b9600637f53456))
* **backend:** use manual batching for ingestion to avoid pickling errors with Redis ([bde435e](https://github.com/jmiguelv/klippy/commit/bde435eb683d4771b6414c718722599612fcff10))
* **backend:** use model_name to bypass strict openai model validation ([53f2594](https://github.com/jmiguelv/klippy/commit/53f25943251306102b1ca28d57b1ce96dc392ebe))
* **backend:** use OpenAILike class for custom LLM to prevent gpt-3.5-turbo fallback ([b00a693](https://github.com/jmiguelv/klippy/commit/b00a6935cca4608ce16d57f38b7b9d12d704ba03))
* **backend:** use standalone phoenix service and OTLP tracing ([6cb5b62](https://github.com/jmiguelv/klippy/commit/6cb5b62d3533d8addcf66f295b0f0f0e7060add0))
* commit uv lockfiles and fix Docker PATH for uv ([eceb784](https://github.com/jmiguelv/klippy/commit/eceb7844e6977a5ac079225935c31f90f63ef69c))
* copy uv.lock to docker containers before sync ([6de8105](https://github.com/jmiguelv/klippy/commit/6de81056142f8b96e7967dc3b835c408afe15bda))
* replace hardcoded API URL with env var and expand engine tests ([d1a96fa](https://github.com/jmiguelv/klippy/commit/d1a96fa06f7c752f0af90778551da493f87222b4))


### Performance Improvements

* **backend:** cache /debug/stats responses in Redis ([1b4bead](https://github.com/jmiguelv/klippy/commit/1b4beada2f5e48d2b922b9e3e8ad35e83d98451d))
* **backend:** optimize ingestion for large datasets with parallel workers ([c076ee0](https://github.com/jmiguelv/klippy/commit/c076ee0960fb7415a6054b755a9afce97331fa99))
* **backend:** switch to simple_summarize and reduce k to 10 for faster responses ([7112b13](https://github.com/jmiguelv/klippy/commit/7112b13007bf01ae018b65e72f5cffbee5a89451))
* replace 19 per-field stats requests with single batch endpoint ([f2ee8c4](https://github.com/jmiguelv/klippy/commit/f2ee8c4314345291952993ef1ecc28c33ab77b4c))
