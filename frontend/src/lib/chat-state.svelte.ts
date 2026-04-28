export interface Source {
	source: string;
	url: string;
	title: string;
	score: number;
}

export interface RetrievalStep {
	label: string;
	detail: string;
	t: number | null;
	active?: boolean;
}

export interface Message {
	role: 'user' | 'klippy';
	content: string;
	filters?: Record<string, string>;
	sources?: Source[];
	steps?: RetrievalStep[];
	total_time_ms?: number;
	cached_at?: string;
	is_cached?: boolean;
	context_length?: number;
}

export interface Session {
	id: string;
	title: string;
	messages: Message[];
	filters: Record<string, string>;
	updatedAt: number;
}

function truncate(str: string, n: number) {
	return str.length > n ? str.slice(0, n - 1) + '...' : str;
}

let sessions = $state<Session[]>([]);
let topK = $state(10);
let threshold = $state(0.3);

export const chatState = {
	get sessions() {
		return sessions;
	},

	get topK() {
		return topK;
	},
	set topK(val: number) {
		topK = val;
		if (typeof window !== 'undefined') localStorage.setItem('klippy_top_k', val.toString());
	},

	get threshold() {
		return threshold;
	},
	set threshold(val: number) {
		threshold = val;
		if (typeof window !== 'undefined') localStorage.setItem('klippy_threshold', val.toString());
	},

	loadSessions() {
		if (typeof window === 'undefined') return;
		const stored = localStorage.getItem('klippy_sessions');
		if (stored) {
			sessions = JSON.parse(stored);
			sessions.sort((a, b) => b.updatedAt - a.updatedAt);
		}
		const storedTopK = localStorage.getItem('klippy_top_k');
		if (storedTopK) topK = parseInt(storedTopK, 10);
		const storedThreshold = localStorage.getItem('klippy_threshold');
		if (storedThreshold) threshold = parseFloat(storedThreshold);
	},

	saveSessions() {
		if (typeof window === 'undefined') return;
		localStorage.setItem('klippy_sessions', JSON.stringify(sessions));
	},

	createNewChat(initialQuery = '') {
		const newId = crypto.randomUUID();
		sessions = [
			{
				id: newId,
				title: initialQuery ? truncate(initialQuery, 30) : 'New Chat',
				messages: [],
				filters: {},
				updatedAt: Date.now()
			},
			...sessions
		];
		chatState.saveSessions();
		return newId;
	},

	deleteChat(id: string) {
		sessions = sessions.filter((s) => s.id !== id);
		chatState.saveSessions();
		return sessions[0]?.id ?? null;
	},

	renameChat(id: string, title: string) {
		const s = sessions.find((s) => s.id === id);
		if (!s) return;
		s.title = title;
		s.updatedAt = Date.now();
		chatState.saveSessions();
	}
};
