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

export const chatState = {
	get sessions() {
		return sessions;
	},

	loadSessions() {
		if (typeof window === 'undefined') return;
		const stored = localStorage.getItem('klippy_sessions');
		if (stored) {
			sessions = JSON.parse(stored);
			sessions.sort((a, b) => b.updatedAt - a.updatedAt);
		}
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
