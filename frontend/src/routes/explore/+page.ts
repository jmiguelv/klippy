import { PUBLIC_API_URL } from '$env/static/public';
import type { PageLoad } from './$types';
import type { CorpusStats } from '$lib/corpus-stats';

export const load: PageLoad = async ({ fetch }) => {
    const statsPromise = fetch(`${PUBLIC_API_URL}/corpus/stats`).then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<CorpusStats>;
    });
    return { statsPromise };
};
