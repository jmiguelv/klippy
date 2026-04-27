import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
    toRelativeTime,
    toBarWidth,
    toSortedEntries,
    sortedSourceEntries,
} from './corpus-stats';

describe('toRelativeTime', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        vi.setSystemTime(new Date('2026-04-27T12:00:00Z'));
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('toRelativeTime_null_returnsDash', () => {
        expect(toRelativeTime(null)).toBe('—');
    });

    it('toRelativeTime_today_returnsToday', () => {
        expect(toRelativeTime('2026-04-27')).toBe('today');
    });

    it('toRelativeTime_yesterday_returnsYesterday', () => {
        expect(toRelativeTime('2026-04-26')).toBe('yesterday');
    });

    it('toRelativeTime_sevenDaysAgo_returnsDaysAgo', () => {
        expect(toRelativeTime('2026-04-20')).toBe('7 days ago');
    });

    it('toRelativeTime_thirtyFiveDaysAgo_returnsMonthAgo', () => {
        expect(toRelativeTime('2026-03-23')).toBe('1 month ago');
    });

    it('toRelativeTime_fourHundredDaysAgo_returnsYearAgo', () => {
        expect(toRelativeTime('2025-03-23')).toBe('1 year ago');
    });

    it('toRelativeTime_invalidString_returnsInputString', () => {
        expect(toRelativeTime('not-a-date')).toBe('not-a-date');
    });
});

describe('toBarWidth', () => {
    it('toBarWidth_zeroMax_returnsZeroPercent', () => {
        expect(toBarWidth(5, 0)).toBe('0%');
    });

    it('toBarWidth_equalToMax_returns100Percent', () => {
        expect(toBarWidth(10, 10)).toBe('100%');
    });

    it('toBarWidth_half_returns50Percent', () => {
        expect(toBarWidth(5, 10)).toBe('50%');
    });

    it('toBarWidth_roundsToNearestPercent', () => {
        expect(toBarWidth(1, 3)).toBe('33%');
    });
});

describe('toSortedEntries', () => {
    it('toSortedEntries_sortsDescending', () => {
        const result = toSortedEntries({ task: 500, doc: 320, issue: 200 });
        expect(result).toEqual([['task', 500], ['doc', 320], ['issue', 200]]);
    });

    it('toSortedEntries_emptyObject_returnsEmpty', () => {
        expect(toSortedEntries({})).toEqual([]);
    });
});

describe('sortedSourceEntries', () => {
    it('sortedSourceEntries_sortsByNodeCountDescending', () => {
        const result = sortedSourceEntries({
            GitHub: { nodes: 300, top_keywords: [] },
            ClickUp: { nodes: 700, top_keywords: [] },
        });
        expect(result[0][0]).toBe('ClickUp');
        expect(result[1][0]).toBe('GitHub');
    });
});
