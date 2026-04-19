import { describe, it, expect } from 'vitest';
import { KNOWN_FIELDS } from './filters';

describe('KNOWN_FIELDS', () => {
	it('should contain expected metadata fields', () => {
		expect(KNOWN_FIELDS).toContain('source');
		expect(KNOWN_FIELDS).toContain('status');
		expect(KNOWN_FIELDS).toContain('repo');
	});

	it('should be an array of strings', () => {
		expect(Array.isArray(KNOWN_FIELDS)).toBe(true);
		expect(typeof KNOWN_FIELDS[0]).toBe('string');
	});
});
