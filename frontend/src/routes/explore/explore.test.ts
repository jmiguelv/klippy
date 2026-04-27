import { describe, it, expect, vi } from 'vitest';
import { load } from './+page';

vi.mock('$env/static/public', () => ({ PUBLIC_API_URL: 'http://localhost:8000' }));

describe('load', () => {
    it('load_okResponse_statsPromiseResolvesToStats', async () => {
        const mockStats = {
            overview: { total_nodes: 42, sources: ['GitHub'], last_ingested: '2026-01-01', date_range: { from: '2024-01-01', to: '2026-01-01' } },
            keywords: { top: [{ keyword: 'RAG', count: 10 }] },
            by_source: { GitHub: { nodes: 42, top_keywords: ['rag'] } },
            by_type: { readme: 42 },
        };
        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => mockStats,
        });

        const result = await load({ fetch: mockFetch } as any);
        const stats = await result.statsPromise;
        expect(stats.overview.total_nodes).toBe(42);
        expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/corpus/stats');
    });

    it('load_errorResponse_statsPromiseRejects', async () => {
        const mockFetch = vi.fn().mockResolvedValue({ ok: false, status: 503 });

        const result = await load({ fetch: mockFetch } as any);
        await expect(result.statsPromise).rejects.toThrow('HTTP 503');
    });
});
