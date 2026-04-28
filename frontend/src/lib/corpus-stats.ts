export interface KeywordCount {
    keyword: string;
    count: number;
}

export interface SourceStats {
    nodes: number;
    top_keywords: string[];
}

export interface CorpusStats {
    overview: {
        total_nodes: number;
        sources: string[];
        last_ingested: string | null;
        date_range: { from: string | null; to: string | null };
    };
    keywords: { top: KeywordCount[] };
    by_source: Record<string, SourceStats>;
    by_type: Record<string, number>;
}

export function toRelativeTime(isoString: string | null): string {
    if (!isoString) return '—';
    const then = new Date(isoString).getTime();
    if (isNaN(then)) return isoString;
    const diffMs = Date.now() - then;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 30) return `${diffDays} days ago`;
    const diffMonths = Math.floor(diffDays / 30);
    if (diffMonths < 12) return diffMonths === 1 ? '1 month ago' : `${diffMonths} months ago`;
    const diffYears = Math.floor(diffDays / 365);
    return diffYears === 1 ? '1 year ago' : `${diffYears} years ago`;
}

export function toBarWidth(count: number, maxCount: number): string {
    if (maxCount === 0) return '0%';
    return `${Math.round((count / maxCount) * 100)}%`;
}

export function toSortedEntries(record: Record<string, number>): Array<[string, number]> {
    return Object.entries(record).sort(([, a], [, b]) => b - a);
}

export function sortedSourceEntries(
    bySource: Record<string, SourceStats>
): Array<[string, SourceStats]> {
    return Object.entries(bySource).sort(([, a], [, b]) => b.nodes - a.nodes);
}
