import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import Page from './+page.svelte';

// Mock SvelteKit navigation
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

describe('+page.svelte', () => {
	it('renders the main heading', () => {
		render(Page);
		const heading = screen.getByText(/Ask anything about/i);
		expect(heading).toBeInTheDocument();
	});

	it('renders the search input', () => {
		render(Page);
		const input = screen.getByPlaceholderText(/Ask Klippy…/i);
		expect(input).toBeInTheDocument();
	});
});
