import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import Page from './+page.svelte';
import { chatState } from '$lib/chat-state.svelte';
import * as navigation from '$app/navigation';

// Mock SvelteKit modules
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$env/static/public', () => ({
	PUBLIC_API_URL: 'http://localhost:8000'
}));

// Mock chatState
vi.mock('$lib/chat-state.svelte', () => ({
	chatState: {
		loadSessions: vi.fn(),
		createNewChat: vi.fn(() => 'test-id')
	}
}));

describe('Chats Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		localStorage.clear();
		// Mock fetch
		global.fetch = vi.fn();
	});

	it('should fetch and display questions on mount', async () => {
		global.fetch = vi.fn().mockResolvedValue({
			ok: true,
			json: async () => ({ questions: ['What is Klippy?', 'How it works?'] })
		} as Response);

		render(Page);

		await waitFor(() => {
			expect(screen.getByText('What is Klippy?')).toBeInTheDocument();
			expect(screen.getByText('How it works?')).toBeInTheDocument();
		});
	});

	it('should create a new chat when clicking a question chip', async () => {
		global.fetch = vi.fn().mockResolvedValue({
			ok: true,
			json: async () => ({ questions: ['What is Klippy?'] })
		} as Response);

		render(Page);

		const chip = await screen.findByText('What is Klippy?');
		chip.click();

		expect(chatState.createNewChat).toHaveBeenCalledWith('What is Klippy?');
		expect(navigation.goto).toHaveBeenCalledWith(expect.stringContaining('test-id'));
	});

	it('should handle fetch failure gracefully', async () => {
		global.fetch = vi.fn().mockRejectedValue(new Error('Fetch failed'));

		render(Page);

		// Should not show chips and not crash
		await new Promise((r) => setTimeout(r, 100));
		expect(screen.queryByRole('button', { name: /What is/ })).not.toBeInTheDocument();
	});
});
