# Spec: feat/questions-endpoint

## Goal

During document ingestion, extract representative questions that each text chunk can answer using LlamaIndex's `QuestionsAnsweredExtractor`. Store the questions in Qdrant node metadata. Expose a `/questions` endpoint that returns a random sample. The `/chats` hero page fetches and displays them as clickable placeholder chips.

---

## Backend — ingestion (`backend/engine.py`)

### Add `QuestionsAnsweredExtractor` to the pipeline

`IngestionPipeline` in `ingest_data()` currently has:

```python
pipeline = IngestionPipeline(
    transformations=[
        MarkdownNodeParser(include_metadata=True),
        Settings.embed_model,
    ],
    ...
)
```

Add the extractor between the parser and the embed model:

```python
from llama_index.core.extractors import QuestionsAnsweredExtractor

pipeline = IngestionPipeline(
    transformations=[
        MarkdownNodeParser(include_metadata=True),
        QuestionsAnsweredExtractor(llm=Settings.llm, num_questions=3),
        Settings.embed_model,
    ],
    ...
)
```

`QuestionsAnsweredExtractor` calls the LLM once per node to generate `num_questions` questions. It stores them in:

```
node.metadata["questions_this_excerpt_can_answer"]
```

The value is a newline-separated string (e.g. `"What is X?\nHow does Y work?\nWhen was Z created?"`).

### Important caveats

- **Cost**: this adds one LLM call per node. For a large corpus this is expensive. Consider adding a CLI flag `--extract-questions` and only running the extractor when explicitly requested.
- **Cache**: the existing `IngestionCache` (Redis) will cache node outputs, so re-ingestion without `--force` will not re-run the extractor on unchanged nodes.
- **Batch size**: the existing `batch_size = 100` loop feeds `pipeline.run(documents=batch)`. The extractor operates on nodes (post-parse), not documents, so a 100-doc batch may produce many more nodes. If LLM rate limits are a concern, reduce batch size to 20–50 when extraction is enabled.

---

## Backend — API endpoint (`backend/main.py`)

### `GET /questions?n=5`

Returns a random sample of `n` questions from across the Qdrant collection, using strict filtering to ensure high-quality suggestions.

```python
import random
import re

@app.get("/questions")
def get_questions(n: int = 5):
    """Sample n questions from Qdrant metadata with strict filtering."""
    metadata_key = "questions_this_excerpt_can_answer"
    all_questions: set[str] = set()
    
    question_words = {
        "Are", "Can", "Could", "Did", "Do", "Does", "How", "Is",
        "What", "When", "Where", "Which", "Who", "Whom", "Whose", "Why"
    }

    # Scroll through all points in the collection
    offset = None
    while True:
        result, next_offset = engine.client.scroll(
            collection_name=engine.collection_name,
            with_payload=True,
            limit=200,
            offset=offset,
        )
        for point in result:
            payload = point.payload or {}
            raw = payload.get(metadata_key, "")

            # Check inside _node_content if not at top level
            if not raw and "_node_content" in payload:
                try:
                    content = json.loads(payload["_node_content"])
                    raw = content.get("metadata", {}).get(metadata_key, "")
                except: pass

            if raw:
                # 1. Split into blocks (double newlines)
                blocks = re.split(r"\n\s*\n", raw.strip())
                for block in blocks:
                    # 2. Take the first line (the question)
                    q = block.split("\n")[0].strip()
                    # 3. Clean numbering, bolding, and parentheticals
                    q = re.sub(r"^\d+\.\s+", "", q)
                    q = re.sub(r"^Question:\s*", "", q, flags=re.IGNORECASE)
                    q = q.strip("* ").split("(")[0].strip()
                    
                    # 4. Filter by interrogative words and trailing ?
                    if any(q.startswith(word) for word in question_words) and q.endswith("?"):
                        all_questions.add(q)
        
        if next_offset is None or len(all_questions) > 500:
            break
        offset = next_offset

    sample = random.sample(list(all_questions), min(n, len(all_questions)))
    return {"questions": sample}
```

Notes:
- `engine.client` is the synchronous `qdrant_client.QdrantClient` already initialised in `KlippyEngine.__init__`.
- `engine.collection_name` is `"klippy_data"` by default.
- The scroll loop handles collections of any size.
- Returns `{"questions": []}` when no questions are stored (no extraction has run yet).

---

## Frontend (`frontend/src/routes/chats/+page.svelte`)

### Fetch questions on mount

```ts
let questions = $state<string[]>([]);

onMount(async () => {
  userName = localStorage.getItem('klippy_user_name') ?? '';
  chatState.loadSessions();

  // existing ?q= redirect handling …

  try {
    const res = await fetch(`${PUBLIC_API_URL}/questions?n=5`);
    if (res.ok) {
      const data = await res.json();
      questions = data.questions ?? [];
    }
  } catch {
    // backend offline — show nothing
  }
});
```

### Render chips

Insert below `.empty-description` and above the closing `</div>` of `.empty-hero`:

```svelte
{#if questions.length > 0}
  <div class="question-chips">
    {#each questions as q}
      <button class="question-chip" onclick={() => submitQuestion(q)}>{q}</button>
    {/each}
  </div>
{/if}
```

```ts
function submitQuestion(q: string) {
  const id = chatState.createNewChat(q);
  goto(`/chats/${id}/?q=${encodeURIComponent(q)}`);
}
```

### Styles

```css
.question-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--size-2);
  margin-top: var(--size-4);
}

.question-chip {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: var(--size-2) var(--size-4);
  font-family: var(--font-sans);
  font-size: 0.8rem;
  color: var(--ink-1);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  text-align: left;
  line-height: 1.4;
}

.question-chip:hover {
  border-color: var(--kings-red);
  color: var(--kings-red);
}
```

---

## Dependencies

`QuestionsAnsweredExtractor` is part of `llama-index-core`. No new pip package required. Verify it is importable:

```python
from llama_index.core.extractors import QuestionsAnsweredExtractor
```

If the import fails, it may be in `llama_index.core.node_parser.extractors` — check the installed version.

---

## Testing

### Ingestion

1. Run ingestion with the extractor enabled on a small sample (`--limit 5 --force`).
2. In Qdrant dashboard or via `client.scroll(...)`, confirm points have `questions_this_excerpt_can_answer` in their payload.

### Endpoint

```bash
curl http://localhost:8000/questions?n=5
# → {"questions": ["What is …?", "How does …?", …]}

curl http://localhost:8000/questions?n=5
# → {"questions": []}  # if no extraction has run
```

### Frontend

1. Start the backend with questions in Qdrant.
2. Open `/chats/` — chips should appear below the description.
3. Click a chip — navigates to a new chat with the question pre-filled and sent.
4. Stop the backend. Reload `/chats/` — no chips, no error shown.
5. Run `pnpm check` — no type errors.

## Branch

`feat/questions-endpoint`
