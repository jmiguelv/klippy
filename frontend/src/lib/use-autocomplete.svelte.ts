import { PUBLIC_API_URL } from '$env/static/public';
import { KNOWN_FIELDS } from './filters';

export interface AcState {
	visible: boolean;
	mode: 'field' | 'value';
	field: string;
	partial: string;
	options: string[];
	activeIdx: number;
}

const AC_CACHE_TTL_MS = 3_600_000;
const AC_CACHE_LS_KEY = 'klippy_ac_cache';

let acCache: Record<string, string[]> = {};
let allStatsReady: Promise<void> | null = null;

async function fetchAllStats(): Promise<void> {
	if (typeof window === 'undefined') return;

	try {
		const stored = localStorage.getItem(AC_CACHE_LS_KEY);
		if (stored) {
			const { timestamp, stats } = JSON.parse(stored) as {
				timestamp: number;
				stats: Record<string, string[]>;
			};
			if (Date.now() - timestamp < AC_CACHE_TTL_MS) {
				Object.assign(acCache, stats);
				return;
			}
		}
	} catch {
		/* ignore */
	}

	try {
		const res = await fetch(`${PUBLIC_API_URL}/debug/stats/all`);
		const data = (await res.json()) as Record<string, Record<string, number>>;
		const stats: Record<string, string[]> = {};
		for (const [field, valueCounts] of Object.entries(data)) {
			stats[field] = Object.keys(valueCounts);
		}
		Object.assign(acCache, stats);
		localStorage.setItem(AC_CACHE_LS_KEY, JSON.stringify({ timestamp: Date.now(), stats }));
	} catch {
		/* ignore */
	}
}

async function fetchValues(field: string): Promise<string[]> {
	if (acCache[field] !== undefined) return acCache[field];
	try {
		const res = await fetch(`${PUBLIC_API_URL}/debug/stats?field=${field}`);
		const data = await res.json();
		acCache[field] = Object.keys(data.counts ?? {});
	} catch {
		acCache[field] = [];
	}
	return acCache[field];
}

export function createAutocomplete() {
	let ac = $state<AcState>({
		visible: false,
		mode: 'field',
		field: '',
		partial: '',
		options: [],
		activeIdx: 0
	});

	if (!allStatsReady) {
		allStatsReady = fetchAllStats();
	}

	async function showValueOptions(field: string, partial: string): Promise<void> {
		if (acCache[field] === undefined && allStatsReady) await allStatsReady;
		const values = acCache[field] !== undefined ? acCache[field] : await fetchValues(field);
		const options = values.filter((v) => v.toLowerCase().includes(partial.toLowerCase()));
		ac = { visible: options.length > 0, mode: 'value', field, partial, options, activeIdx: 0 };
	}

	return {
		get state() {
			return ac;
		},
		set state(val: AcState) {
			ac = val;
		},

		async handleInput(text: string, cursor: number) {
			const before = text.slice(0, cursor);

			const valueMatch = before.match(/@(\w+):(?:"([^"]*)"|([^"\s]*))$/);
			const fieldMatch = !valueMatch && before.match(/@(\w*)$/);

			if (valueMatch) {
				const [, field, quoted, unquoted] = valueMatch;
				const partial = quoted ?? unquoted;
				if (acCache[field] !== undefined) {
					await showValueOptions(field, partial);
				} else {
					await fetchValues(field);
					// Re-check after fetch
					await showValueOptions(field, partial);
				}
			} else if (fieldMatch) {
				const [, partial] = fieldMatch;
				const options = KNOWN_FIELDS.filter((f) =>
					f.toLowerCase().includes(partial.toLowerCase())
				);
				ac = {
					visible: options.length > 0,
					mode: 'field',
					field: '',
					partial,
					options,
					activeIdx: 0
				};
			} else {
				ac = { ...ac, visible: false };
			}
		},

		handleKeydown(e: KeyboardEvent, selectCallback: (opt: string) => void) {
			if (!ac.visible) return;

			if (e.key === 'ArrowDown') {
				e.preventDefault();
				ac.activeIdx = (ac.activeIdx + 1) % ac.options.length;
			} else if (e.key === 'ArrowUp') {
				e.preventDefault();
				ac.activeIdx = (ac.activeIdx - 1 + ac.options.length) % ac.options.length;
			} else if (e.key === 'Enter') {
				e.preventDefault();
				selectCallback(ac.options[ac.activeIdx]);
			} else if (e.key === 'Escape') {
				ac.visible = false;
			}
		},

		close() {
			ac.visible = false;
		}
	};
}
