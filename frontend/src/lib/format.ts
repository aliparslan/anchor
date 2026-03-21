/** Format a large number with k/M suffixes (e.g. 1200 -> "1.2k") */
export function formatTokens(n: number): string {
	if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
	if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
	return String(n);
}

/** Format a duration in minutes as "Xh Ym" or "Xh" */
export function formatDuration(mins: number): string {
	const h = Math.floor(mins / 60);
	const m = mins % 60;
	return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

/** Format milliseconds as MM:SS with zero-padding */
export function formatTime(ms: number): string {
	const totalSec = Math.ceil(ms / 1000);
	const m = Math.floor(totalSec / 60);
	const s = totalSec % 60;
	return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
