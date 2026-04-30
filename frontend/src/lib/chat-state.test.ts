import { describe, it, expect, beforeEach } from 'vitest';
import { chatState } from './chat-state.svelte';

describe('chatState', () => {
	beforeEach(() => {
		localStorage.clear();
		// Reset state if possible, but it's a singleton. 
		// For now, let's just test the userName property which I'm about to add.
	});

	it('should manage userName', () => {
		expect(chatState.userName).toBe('');
		chatState.userName = 'Alice';
		expect(chatState.userName).toBe('Alice');
		expect(localStorage.getItem('klippy_user_name')).toBe('Alice');
	});

    it('should load userName from localStorage', () => {
        localStorage.setItem('klippy_user_name', 'Bob');
        chatState.loadSessions(); // This should also load userName
        expect(chatState.userName).toBe('Bob');
    });
});
