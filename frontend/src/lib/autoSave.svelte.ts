/**
 * Creates a reusable debounce-save-then-flash-indicator utility.
 *
 * @param saveFn  – async function that performs the actual save
 * @param delay   – debounce delay in ms (default 1500)
 */
export function createAutoSave(saveFn: () => Promise<void>, delay = 1500) {
	let saving = $state(false);
	let saved = $state(false);
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let indicatorTimeout: ReturnType<typeof setTimeout> | null = null;

	function trigger() {
		if (saveTimeout) clearTimeout(saveTimeout);
		saveTimeout = setTimeout(async () => {
			if (saving) return;
			saving = true;
			try {
				await saveFn();
				saved = true;
				if (indicatorTimeout) clearTimeout(indicatorTimeout);
				indicatorTimeout = setTimeout(() => {
					saved = false;
				}, 2000);
			} catch {
				// caller handles errors in saveFn if needed
			} finally {
				saving = false;
			}
		}, delay);
	}

	function cleanup() {
		if (saveTimeout) clearTimeout(saveTimeout);
		if (indicatorTimeout) clearTimeout(indicatorTimeout);
	}

	return {
		get saving() { return saving; },
		get saved() { return saved; },
		trigger,
		cleanup
	};
}
