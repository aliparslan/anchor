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

export async function fetchHnPosts(): Promise<HnPost[]> {
	const res = await fetch(`${BASE}/api/hn`);
	const data = await res.json();
	return data.posts;
}

export async function fetchYoutubeVideos(): Promise<YoutubeVideo[]> {
	const res = await fetch(`${BASE}/api/youtube`);
	const data = await res.json();
	return data.videos;
}

export async function refreshHn(): Promise<HnPost[]> {
	const res = await fetch(`${BASE}/api/refresh/hn`, { method: 'POST' });
	const data = await res.json();
	return data.posts;
}

export async function refreshYoutube(): Promise<YoutubeVideo[]> {
	const res = await fetch(`${BASE}/api/refresh/youtube`, { method: 'POST' });
	const data = await res.json();
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
	const res = await fetch(url);
	const data = await res.json();
	return data.entry;
}

export async function saveJournal(date: string, content: string): Promise<JournalEntry> {
	const res = await fetch(`${BASE}/api/journal/${date}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ content })
	});
	const data = await res.json();
	return data.entry;
}

export async function fetchJournalDates(): Promise<string[]> {
	const res = await fetch(`${BASE}/api/journal/dates`);
	const data = await res.json();
	return data.dates;
}

export async function fetchPomodoroToday(): Promise<{ sessions: PomodoroSession[]; total_minutes: number }> {
	const res = await fetch(`${BASE}/api/pomodoro/today`);
	return res.json();
}

export async function completePomodoroSession(): Promise<{ sessions: PomodoroSession[]; total_minutes: number }> {
	const res = await fetch(`${BASE}/api/pomodoro/complete`, { method: 'POST' });
	return res.json();
}

export interface WeatherData {
	temp: number;
	weather_code: number;
	high: number;
	low: number;
	rain_chance: number;
}

export async function fetchWeather(): Promise<{ weather: WeatherData | null; zip_code: string | null; location: string }> {
	const res = await fetch(`${BASE}/api/weather`);
	return res.json();
}

export async function setWeatherZip(zip_code: string): Promise<{ weather: WeatherData | null; zip_code: string; location: string; error?: string }> {
	const res = await fetch(`${BASE}/api/weather/zip`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ zip_code })
	});
	return res.json();
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
	const res = await fetch(`${BASE}/api/habits/today`);
	return res.json();
}

export async function toggleHabit(habit: string): Promise<boolean> {
	const res = await fetch(`${BASE}/api/habits/toggle/${habit}`, { method: 'POST' });
	const data = await res.json();
	return data.done;
}

export async function fetchDismissedVideoIds(): Promise<string[]> {
	const res = await fetch(`${BASE}/api/videos/dismissed`);
	const data = await res.json();
	return data.dismissed;
}

export async function dismissVideoServer(videoId: string): Promise<void> {
	await fetch(`${BASE}/api/videos/dismiss/${encodeURIComponent(videoId)}`, { method: 'POST' });
}

export async function fetchVapidPublicKey(): Promise<string> {
	const res = await fetch(`${BASE}/api/push/vapid-key`);
	const data = await res.json();
	return data.public_key;
}

export async function registerPushSubscription(sub: PushSubscriptionJSON): Promise<void> {
	await fetch(`${BASE}/api/push/subscribe`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			endpoint: sub.endpoint,
			p256dh: sub.keys!.p256dh,
			auth: sub.keys!.auth
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

export interface Capture {
	id: number;
	text: string;
	created_at: string;
	archived_at: string | null;
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
	const res = await fetch(`${BASE}/api/mit/today`);
	const data = await res.json();
	return data.mit;
}

export async function saveMit(text: string): Promise<Mit> {
	const res = await fetch(`${BASE}/api/mit/today`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ text })
	});
	const data = await res.json();
	return data.mit;
}

export async function toggleMit(): Promise<boolean> {
	const res = await fetch(`${BASE}/api/mit/today/toggle`, { method: 'POST' });
	const data = await res.json();
	return data.completed;
}

// --- Reading Queue ---

export async function fetchReadingQueue(): Promise<ReadingQueueItem[]> {
	const res = await fetch(`${BASE}/api/reading-queue`);
	const data = await res.json();
	return data.items;
}

export async function saveToReadingQueue(item: { hn_id?: number; title: string; url: string; domain?: string }): Promise<ReadingQueueItem> {
	const res = await fetch(`${BASE}/api/reading-queue`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(item)
	});
	const data = await res.json();
	return data.item;
}

export async function markQueueItemRead(id: number): Promise<void> {
	await fetch(`${BASE}/api/reading-queue/${id}/read`, { method: 'POST' });
}

export async function deleteQueueItem(id: number): Promise<void> {
	await fetch(`${BASE}/api/reading-queue/${id}`, { method: 'DELETE' });
}

// --- Sleep ---

export async function fetchSleepToday(): Promise<SleepLog | null> {
	const res = await fetch(`${BASE}/api/sleep/today`);
	const data = await res.json();
	return data.sleep;
}

export async function saveSleep(bedtime: string, wake_time: string): Promise<SleepLog> {
	const res = await fetch(`${BASE}/api/sleep/today`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ bedtime, wake_time })
	});
	const data = await res.json();
	return data.sleep;
}

// --- Workout ---

export async function fetchWorkoutToday(): Promise<Workout | null> {
	const res = await fetch(`${BASE}/api/workout/today`);
	const data = await res.json();
	return data.workout;
}

export async function toggleWorkout(): Promise<boolean> {
	const res = await fetch(`${BASE}/api/workout/today/toggle`, { method: 'POST' });
	const data = await res.json();
	return data.completed;
}

export async function saveWorkoutNote(note: string): Promise<Workout> {
	const res = await fetch(`${BASE}/api/workout/today`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ note })
	});
	const data = await res.json();
	return data.workout;
}

// --- Mood ---

export async function fetchMoodToday(): Promise<MoodLog | null> {
	const res = await fetch(`${BASE}/api/mood/today`);
	const data = await res.json();
	return data.mood;
}

export async function saveMood(mood: number): Promise<MoodLog> {
	const res = await fetch(`${BASE}/api/mood/today`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ mood })
	});
	const data = await res.json();
	return data.mood;
}

// --- Quick Capture ---

export async function fetchCaptures(): Promise<Capture[]> {
	const res = await fetch(`${BASE}/api/captures`);
	const data = await res.json();
	return data.captures;
}

export async function saveCapture(text: string): Promise<Capture> {
	const res = await fetch(`${BASE}/api/captures`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ text })
	});
	const data = await res.json();
	return data.capture;
}

export async function archiveCapture(id: number): Promise<void> {
	await fetch(`${BASE}/api/captures/${id}/archive`, { method: 'POST' });
}

export async function deleteCapture(id: number): Promise<void> {
	await fetch(`${BASE}/api/captures/${id}`, { method: 'DELETE' });
}

// --- Custom Habits ---

export async function fetchCustomHabits(): Promise<CustomHabit[]> {
	const res = await fetch(`${BASE}/api/habits/custom`);
	const data = await res.json();
	return data.habits;
}

export async function addCustomHabit(name: string): Promise<CustomHabit> {
	const res = await fetch(`${BASE}/api/habits/custom`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name })
	});
	const data = await res.json();
	return data.habit;
}

export async function deleteCustomHabit(id: number): Promise<void> {
	await fetch(`${BASE}/api/habits/custom/${id}`, { method: 'DELETE' });
}

// --- Aggregation ---

export async function fetchDaySummary(): Promise<DaySummary> {
	const res = await fetch(`${BASE}/api/summary/today`);
	return res.json();
}

export async function fetchHabitsWeek(): Promise<HabitsWeek> {
	const res = await fetch(`${BASE}/api/habits/week`);
	return res.json();
}

export async function fetchStreaks(): Promise<Record<string, number>> {
	const res = await fetch(`${BASE}/api/habits/streaks`);
	const data = await res.json();
	return data.streaks;
}

export async function fetchWeeklyReview(): Promise<WeeklyReview> {
	const res = await fetch(`${BASE}/api/review/week`);
	return res.json();
}
