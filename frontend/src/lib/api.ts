export interface HnPost {
	id: number;
	hn_id: number;
	title: string;
	url: string;
	domain: string;
	score: number;
	comments: number;
	hn_url: string;
	fetched_at: string;
}

export interface YoutubeVideo {
	id: number;
	video_id: string;
	title: string;
	channel: string;
	thumbnail: string;
	duration_seconds: number;
	duration_label: string;
	fetched_at: string;
}

const BASE = '';

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
	const res = await fetch(url, init);
	if (!res.ok) throw new Error(`API error ${res.status}: ${url}`);
	return res.json();
}

export async function fetchHnPosts(): Promise<HnPost[]> {
	const data = await apiFetch<{ posts: HnPost[] }>(`${BASE}/api/hn`);
	return data.posts;
}

export async function fetchYoutubeVideos(): Promise<YoutubeVideo[]> {
	const data = await apiFetch<{ videos: YoutubeVideo[] }>(`${BASE}/api/youtube`);
	return data.videos;
}

export async function refreshHn(): Promise<HnPost[]> {
	const data = await apiFetch<{ posts: HnPost[] }>(`${BASE}/api/refresh/hn`, { method: 'POST' });
	return data.posts;
}

export async function refreshYoutube(): Promise<YoutubeVideo[]> {
	const data = await apiFetch<{ videos: YoutubeVideo[] }>(`${BASE}/api/refresh/youtube`, { method: 'POST' });
	return data.videos;
}

export interface JournalEntry {
	date: string;
	content: string;
	updated_at: string;
}

export interface PomodoroSession {
	id: number;
	date: string;
	completed_at: string;
	duration_minutes: number;
}

export async function fetchJournal(date?: string): Promise<JournalEntry | null> {
	const url = date ? `${BASE}/api/journal/${date}` : `${BASE}/api/journal/today`;
	const data = await apiFetch<{ entry: JournalEntry | null }>(url);
	return data.entry;
}

export async function saveJournal(date: string, content: string): Promise<JournalEntry> {
	const data = await apiFetch<{ entry: JournalEntry }>(`${BASE}/api/journal/${date}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ content })
	});
	return data.entry;
}

export async function appendJournalToday(text: string): Promise<JournalEntry> {
	const data = await apiFetch<{ entry: JournalEntry }>(`${BASE}/api/journal/today/append`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ content: text })
	});
	return data.entry;
}

export async function fetchJournalDates(): Promise<string[]> {
	const data = await apiFetch<{ dates: string[] }>(`${BASE}/api/journal/dates`);
	return data.dates;
}
export interface JournalPreview { date: string; preview: string; }
export async function fetchJournalEntries(limit = 20, offset = 0): Promise<JournalPreview[]> {
	const data = await apiFetch<{ entries: JournalPreview[] }>(`${BASE}/api/journal/entries?limit=${limit}&offset=${offset}`);
	return data.entries;
}

export async function fetchPomodoroToday(): Promise<{ sessions: PomodoroSession[]; total_minutes: number }> {
	return apiFetch(`${BASE}/api/pomodoro/today`);
}

export async function completePomodoroSession(): Promise<{ sessions: PomodoroSession[]; total_minutes: number }> {
	return apiFetch(`${BASE}/api/pomodoro/complete`, { method: 'POST' });
}

export interface WeatherHour {
	time: string;
	temp: number;
	condition: string;
	weather_code: number;
}

export interface WeatherData {
	temp: number;
	weather_code: number;
	condition: string;
	high: number;
	low: number;
	rain_chance: number;
	hourly: WeatherHour[];
}

export async function fetchWeather(): Promise<{ weather: WeatherData | null; zip_code: string | null; location: string }> {
	return apiFetch(`${BASE}/api/weather`);
}

export async function setWeatherZip(zip_code: string): Promise<{ weather: WeatherData | null; zip_code: string; location: string; error?: string }> {
	return apiFetch(`${BASE}/api/weather/zip`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ zip_code })
	});
}

export interface HabitsToday {
	date: string;
	focus_minutes: number;
	focus_achieved: boolean;
	workout: number;
	night_routine: boolean;
	sleep_tracked: boolean;
	mood_logged: boolean;
	custom_habits: Record<string, boolean>;
}

export interface CustomHabit {
	id: number;
	name: string;
	created_at: string;
}

export async function fetchHabitsToday(): Promise<HabitsToday> {
	return apiFetch(`${BASE}/api/habits/today`);
}

export async function toggleHabit(habit: string): Promise<boolean> {
	const data = await apiFetch<{ done: boolean }>(`${BASE}/api/habits/toggle/${habit}`, { method: 'POST' });
	return data.done;
}

export async function fetchDismissedVideoIds(): Promise<string[]> {
	const data = await apiFetch<{ dismissed: string[] }>(`${BASE}/api/videos/dismissed`);
	return data.dismissed;
}

export async function dismissVideoServer(videoId: string): Promise<void> {
	await apiFetch(`${BASE}/api/videos/dismiss/${encodeURIComponent(videoId)}`, { method: 'POST' });
}

export async function fetchVapidPublicKey(): Promise<string> {
	const data = await apiFetch<{ public_key: string }>(`${BASE}/api/push/vapid-key`);
	return data.public_key;
}

export async function registerPushSubscription(sub: PushSubscriptionJSON): Promise<void> {
	if (!sub.keys) return;
	await apiFetch(`${BASE}/api/push/subscribe`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			endpoint: sub.endpoint,
			p256dh: sub.keys.p256dh,
			auth: sub.keys.auth
		})
	});
}

// --- New interfaces ---

export interface Mit {
	date: string;
	text: string;
	completed: number;
	updated_at: string;
}

export interface ReadingQueueItem {
	id: number;
	hn_id: number | null;
	title: string;
	url: string;
	domain: string | null;
	saved_at: string;
	read_at: string | null;
}

export interface SleepLog {
	date: string;
	bedtime: string | null;
	wake_time: string | null;
	updated_at: string;
}

export interface Workout {
	date: string;
	completed: number;
	note: string;
	updated_at: string;
}

export interface MoodLog {
	date: string;
	mood: number;
	updated_at: string;
}

export interface DaySummary {
	mit: { text: string; completed: number } | null;
	focus_minutes: number;
	habits: { name: string; done: boolean }[];
	journal_written: boolean;
	mood: number | null;
	sleep: { bedtime: string | null; wake_time: string | null } | null;
	workout: { completed: number; note: string } | null;
}

export interface WeeklyReview {
	focus_hours: number;
	habit_rate: { completed: number; total: number };
	mood_trend: (number | null)[];
	mit_rate: { completed: number; total: number };
	avg_sleep_hours: number | null;
	focus_per_day: number[];
}

export interface HabitsWeek {
	dates: string[];
	habits: Record<string, boolean[]>;
}

// --- MIT ---

export async function fetchMitToday(): Promise<Mit | null> {
	const data = await apiFetch<{ mit: Mit | null }>(`${BASE}/api/mit/today`);
	return data.mit;
}

export async function saveMit(text: string): Promise<Mit> {
	const data = await apiFetch<{ mit: Mit }>(`${BASE}/api/mit/today`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ text })
	});
	return data.mit;
}

export async function toggleMit(): Promise<boolean> {
	const data = await apiFetch<{ completed: boolean }>(`${BASE}/api/mit/today/toggle`, { method: 'POST' });
	return data.completed;
}

// --- Reading Queue ---

export async function fetchReadingQueue(): Promise<ReadingQueueItem[]> {
	const data = await apiFetch<{ items: ReadingQueueItem[] }>(`${BASE}/api/reading-queue`);
	return data.items;
}

export async function saveToReadingQueue(item: { hn_id?: number; title: string; url: string; domain?: string }): Promise<ReadingQueueItem> {
	const data = await apiFetch<{ item: ReadingQueueItem }>(`${BASE}/api/reading-queue`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(item)
	});
	return data.item;
}

export async function markQueueItemRead(id: number): Promise<void> {
	await apiFetch(`${BASE}/api/reading-queue/${id}/read`, { method: 'POST' });
}

export async function deleteQueueItem(id: number): Promise<void> {
	await apiFetch(`${BASE}/api/reading-queue/${id}`, { method: 'DELETE' });
}

export async function deleteQueueItemByHnId(hnId: number): Promise<void> {
	await apiFetch(`${BASE}/api/reading-queue/by-hn/${hnId}`, { method: 'DELETE' });
}

export async function markQueueItemUnread(id: number): Promise<void> {
	await apiFetch(`${BASE}/api/reading-queue/${id}/unread`, { method: 'POST' });
}

// --- Sleep ---

export interface SleepDay {
	date: string;
	bedtime: string | null;
	wake_time: string | null;
}

export async function fetchSleepWeek(): Promise<SleepDay[]> {
	const data = await apiFetch<{ days: SleepDay[] }>(`${BASE}/api/sleep/week`);
	return data.days;
}

export async function fetchSleepToday(): Promise<SleepLog | null> {
	const data = await apiFetch<{ sleep: SleepLog | null }>(`${BASE}/api/sleep/today`);
	return data.sleep;
}

export async function saveSleep(bedtime: string, wake_time: string): Promise<SleepLog> {
	const data = await apiFetch<{ sleep: SleepLog }>(`${BASE}/api/sleep/today`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ bedtime, wake_time })
	});
	return data.sleep;
}

// --- Workout ---

export async function fetchWorkoutToday(): Promise<Workout | null> {
	const data = await apiFetch<{ workout: Workout | null }>(`${BASE}/api/workout/today`);
	return data.workout;
}

export async function toggleWorkout(): Promise<boolean> {
	const data = await apiFetch<{ completed: boolean }>(`${BASE}/api/workout/today/toggle`, { method: 'POST' });
	return data.completed;
}

export async function saveWorkoutNote(note: string): Promise<Workout> {
	const data = await apiFetch<{ workout: Workout }>(`${BASE}/api/workout/today`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ note })
	});
	return data.workout;
}

// --- Mood ---

export async function fetchMoodToday(): Promise<MoodLog | null> {
	const data = await apiFetch<{ mood: MoodLog | null }>(`${BASE}/api/mood/today`);
	return data.mood;
}

export async function saveMood(mood: number): Promise<MoodLog> {
	const data = await apiFetch<{ mood: MoodLog }>(`${BASE}/api/mood/today`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ mood })
	});
	return data.mood;
}

// --- Custom Habits ---

export async function fetchCustomHabits(): Promise<CustomHabit[]> {
	const data = await apiFetch<{ habits: CustomHabit[] }>(`${BASE}/api/habits/custom`);
	return data.habits;
}

export async function addCustomHabit(name: string): Promise<CustomHabit> {
	const data = await apiFetch<{ habit: CustomHabit }>(`${BASE}/api/habits/custom`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name })
	});
	return data.habit;
}

export async function deleteCustomHabit(id: number): Promise<void> {
	await apiFetch(`${BASE}/api/habits/custom/${id}`, { method: 'DELETE' });
}

// --- Aggregation ---

export async function fetchDaySummary(): Promise<DaySummary> {
	return apiFetch(`${BASE}/api/summary/today`);
}

export async function fetchHabitsWeek(): Promise<HabitsWeek> {
	return apiFetch(`${BASE}/api/habits/week`);
}

export async function fetchStreaks(): Promise<Record<string, number>> {
	const data = await apiFetch<{ streaks: Record<string, number> }>(`${BASE}/api/habits/streaks`);
	return data.streaks;
}

export async function fetchWeeklyReview(): Promise<WeeklyReview> {
	return apiFetch(`${BASE}/api/review/week`);
}

export interface FocusDay {
	date: string;
	minutes: number;
}

export async function fetchFocusMonth(): Promise<FocusDay[]> {
	const data = await apiFetch<{ days: FocusDay[] }>(`${BASE}/api/focus/month`);
	return data.days;
}

export async function fetchDailyStreak(): Promise<number> {
	const data = await apiFetch<{ streak: number }>(`${BASE}/api/streak`);
	return data.streak;
}

export interface DailyScore {
	score: number;
	breakdown: { mit: number; focus: number; habits: number; journal: number; mood: number };
}

export async function fetchDailyScore(): Promise<DailyScore> {
	return apiFetch(`${BASE}/api/score/today`);
}

// --- RSS ---

export interface RssItem {
	id: number;
	feed_name: string;
	site_url: string;
	title: string;
	url: string;
	author: string;
	published_at: string;
	fetched_at: string;
}

export async function fetchRssItems(): Promise<RssItem[]> {
	const data = await apiFetch<{ items: RssItem[] }>(`${BASE}/api/rss`);
	return data.items;
}

export async function refreshRss(): Promise<RssItem[]> {
	const data = await apiFetch<{ items: RssItem[] }>(`${BASE}/api/refresh/rss`, { method: 'POST' });
	return data.items;
}

// --- Status ---

export interface SystemStatus {
	hostname: string;
	uptime: string;
	cpu_percent: number;
	memory: { total_gb: number; used_gb: number; percent: number };
	disk: { total_gb: number; used_gb: number; percent: number };
}

export interface ClaudeStatus {
	available: boolean;
	total_messages?: number;
	total_sessions?: number;
	daily_activity?: { date: string; messageCount: number; sessionCount: number; toolCallCount: number }[];
	model_usage?: Record<string, { inputTokens: number; outputTokens: number; cacheReadInputTokens: number; cacheCreationInputTokens: number }>;
	last_computed?: string;
}

export interface TailscaleDevice {
	hostname: string;
	os: string;
	online: boolean;
	ip: string;
}

export interface TailscaleStatus {
	available: boolean;
	self?: { hostname: string; ip: string; online: boolean };
	peers?: TailscaleDevice[];
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
	return apiFetch(`${BASE}/api/status/system`);
}

export async function fetchClaudeStatus(): Promise<ClaudeStatus> {
	return apiFetch(`${BASE}/api/status/claude`);
}

export async function fetchTailscaleStatus(): Promise<TailscaleStatus> {
	return apiFetch(`${BASE}/api/status/tailscale`);
}

// --- Water ---
export async function fetchWaterToday(): Promise<number> {
	const data = await apiFetch<{ glasses: number }>(`${BASE}/api/water/today`);
	return data.glasses;
}
export async function incrementWater(): Promise<number> {
	const data = await apiFetch<{ glasses: number }>(`${BASE}/api/water/increment`, { method: 'POST' });
	return data.glasses;
}
export async function decrementWater(): Promise<number> {
	const data = await apiFetch<{ glasses: number }>(`${BASE}/api/water/decrement`, { method: 'POST' });
	return data.glasses;
}
export async function setWater(glasses: number): Promise<number> {
	const data = await apiFetch<{ glasses: number }>(`${BASE}/api/water/set`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ glasses })
	});
	return data.glasses;
}
export interface WaterDay { date: string; glasses: number; }
export async function fetchWaterWeek(): Promise<WaterDay[]> {
	return apiFetch<WaterDay[]>(`${BASE}/api/water/week`);
}

// --- Gratitude ---
export interface GratitudeEntry { id: number; text: string; created_at: string; }
export async function fetchGratitudes(): Promise<GratitudeEntry[]> {
	const data = await apiFetch<{ items: GratitudeEntry[] }>(`${BASE}/api/gratitude`);
	return data.items;
}
export async function saveGratitude(text: string): Promise<GratitudeEntry> {
	const data = await apiFetch<{ item: GratitudeEntry }>(`${BASE}/api/gratitude`, {
		method: 'POST', headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ text })
	});
	return data.item;
}
export async function fetchRandomGratitude(): Promise<GratitudeEntry | null> {
	const data = await apiFetch<{ item: GratitudeEntry | null }>(`${BASE}/api/gratitude/random`);
	return data.item;
}

// --- Search ---
export interface SearchResults {
	journal: { date: string; content: string }[];
	queue: { id: number; title: string; url: string; domain: string }[];
	rss: { id: number; title: string; url: string; feed_name: string }[];
}
export async function searchAll(query: string): Promise<SearchResults> {
	const data = await apiFetch<{ results: SearchResults }>(`${BASE}/api/search?q=${encodeURIComponent(query)}`);
	return data.results;
}

export async function fetchDashboardAge(): Promise<{ days: number; since: string }> {
	return apiFetch(`${BASE}/api/status/age`);
}

// --- Achievements ---
export interface Achievement { id: number; name: string; description: string; earned_at: string; }
export async function fetchAchievements(): Promise<{ achievements: Achievement[]; new: Achievement[] }> {
	return apiFetch(`${BASE}/api/achievements`);
}
