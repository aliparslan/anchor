/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />
/// <reference types="@sveltejs/kit" />

import { build, files, version } from '$service-worker';

const self = /** @type {ServiceWorkerGlobalScope} */ (/** @type {unknown} */ (globalThis));
const CACHE = `anchor-${version}`;
const ASSETS = [...build, ...files];

// Precache all app assets on install
self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE).then((cache) => cache.addAll(ASSETS))
	);
});

// Clean old caches on activate
self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((keys) =>
			Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
		).then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	if (event.request.method !== 'GET') return;

	const url = new URL(event.request.url);

	// Never cache API calls
	if (url.pathname.startsWith('/api')) return;

	event.respondWith(respond(event, url));
});

async function respond(event, url) {
	const cache = await caches.open(CACHE);

	// Precached assets — always serve from cache
	if (ASSETS.includes(url.pathname)) {
		const cached = await cache.match(url.pathname);
		if (cached) return cached;
	}

	// Everything else — network first, cache fallback
	try {
		const response = await fetch(event.request);
		if (!(response instanceof Response)) throw new Error('invalid response');
		if (response.status === 200) {
			cache.put(event.request, response.clone());
		}
		return response;
	} catch {
		const cached = await cache.match(event.request);
		if (cached) return cached;

		// Offline fallback for navigation requests
		if (event.request.mode === 'navigate') {
			const fallback = await cache.match('/');
			if (fallback) return fallback;
		}

		throw new Error('offline');
	}
}

// Push notifications
self.addEventListener('push', (event) => {
	const data = event.data ? event.data.json() : { title: 'Anchor', body: 'Timer complete!' };
	event.waitUntil(
		self.registration.showNotification(data.title, {
			body: data.body,
			icon: '/icon-192.png',
			badge: '/icon-192.png',
			tag: 'anchor-timer',
			vibrate: [200, 100, 200]
		})
	);
});
