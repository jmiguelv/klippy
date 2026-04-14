# Chat Interface Implementation Plan

This document outlines the steps required to transition Klippy from a single-query search interface to a fully conversational Retrieval-Augmented Generation (RAG) chat interface.

## 1. Backend Engine Updates (`backend/engine.py`)

Currently, Klippy uses an `as_query_engine()` which processes each request in isolation. We need to switch to a chat engine to maintain conversational context.

*   **Switch to Chat Engine:** Change `get_query_engine()` to `get_chat_engine()`.
*   **Use `condense_plus_context` Mode:** Initialize the chat engine using `self._index.as_chat_engine(chat_mode="condense_plus_context", llm=Settings.llm, ...)`. This mode is ideal because it uses the LLM to rewrite the user's latest message using the chat history to provide context, searches the vector database with that condensed question, and then generates a response.
*   **Memory Management:** The chat engine needs a `memory` component (e.g., `ChatMemoryBuffer`) to store the conversation history.

## 2. Backend API & State Updates (`backend/main.py`)

The FastAPI endpoints must be updated to handle conversation sessions rather than isolated queries.

*   **Session Management:** Update the `QueryRequest` model to include an optional `session_id`. If not provided, the backend generates one.
*   **Redis Updates:** 
    *   Instead of caching a single answer per query string, Redis will store the serialized chat history (the `ChatMemoryBuffer`) associated with the `session_id`.
    *   When a request comes in, the backend retrieves the history for that `session_id`, passes it to the chat engine, executes the turn, and saves the updated history back to Redis.
*   **Feedback Mechanism:** The `/feedback` endpoint will need to accept a `session_id` and a `message_id` (or index) to flag specific responses in the history.

## 3. Frontend UI Updates (`frontend/src/pages/index.astro`)

The frontend requires significant structural changes to support a continuous dialogue.

*   **Layout Changes:** Replace the single `answer-block` with a scrollable `chat-container` that holds a list of message bubbles.
*   **Message Bubbles:** Create distinct styles for "User" messages (right-aligned, solid color) and "Klippy" messages (left-aligned, card style).
*   **Javascript Logic:** 
    *   Generate and store a `session_id` in `localStorage` or `sessionStorage`.
    *   Update `handleSearch()` to append the user's message to the DOM immediately, display a typing indicator in a new Klippy bubble, and then stream or await the response.
    *   Parse the Markdown and sources for each individual Klippy response bubble.
    *   Attach the timing metadata, cache badges, and thumbs up/down buttons to the specific Klippy message bubble they belong to.
*   **Streaming (Optional but Recommended):** To improve perceived latency in a chat context, consider updating the FastAPI backend to return a `StreamingResponse` and the Astro frontend to consume Server-Sent Events (SSE) so the text appears as it's generated.

## 4. Prompt & Configuration Relocation

*   **Move Prompt:** The `prompt.md` file will be moved from `data/final/` to a dedicated `config/` directory at the project root to properly separate application configuration from harvested data.
*   **Update Paths:** `backend/engine.py` and `docker-compose.yml` will be updated to point to and mount this new `config/` directory.
