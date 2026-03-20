export function tap() {
	if ('vibrate' in navigator) navigator.vibrate(10);
}

export function success() {
	if ('vibrate' in navigator) navigator.vibrate([10, 30, 10]);
}

export function heavy() {
	if ('vibrate' in navigator) navigator.vibrate(20);
}
