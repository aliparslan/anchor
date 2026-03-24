/** Global toast notification state */

export interface Toast {
	id: number;
	message: string;
	type: 'info' | 'success' | 'error';
}

let nextId = 0;
let toasts = $state<Toast[]>([]);

export function getToasts(): Toast[] {
	return toasts;
}

export function showToast(message: string, type: Toast['type'] = 'info', duration = 3000) {
	const id = nextId++;
	toasts = [...toasts, { id, message, type }];
	setTimeout(() => {
		toasts = toasts.filter((t) => t.id !== id);
	}, duration);
}

export function dismissToast(id: number) {
	toasts = toasts.filter((t) => t.id !== id);
}
