const canHaptic = typeof window !== 'undefined'
	&& window.matchMedia('(pointer: coarse)').matches;

const hasVibrate = typeof navigator !== 'undefined' && 'vibrate' in navigator;

function iosHaptic() {
	const input = document.createElement('input');
	input.type = 'checkbox';
	input.setAttribute('switch', '');
	input.style.cssText = 'position:fixed;top:-100px;opacity:0;pointer-events:none';

	const label = document.createElement('label');
	label.style.cssText = 'position:fixed;top:-100px;opacity:0;pointer-events:none';
	label.appendChild(input);

	document.body.appendChild(label);
	label.click();
	requestAnimationFrame(() => label.remove());
}

function vibrate(pattern: number | number[]) {
	if (!canHaptic) return;
	if (hasVibrate) {
		navigator.vibrate(pattern);
	} else {
		iosHaptic();
	}
}

export function tap() {
	vibrate(10);
}

export function success() {
	if (!canHaptic) return;
	if (hasVibrate) {
		navigator.vibrate([10, 30, 10]);
	} else {
		iosHaptic();
		setTimeout(iosHaptic, 80);
	}
}

export function heavy() {
	vibrate(20);
}
