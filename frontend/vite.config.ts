import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const useHttps = process.env.VITE_HTTPS !== 'false';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		...(useHttps && {
			https: {
				key: '../backend/cert.key',
				cert: '../backend/cert.crt'
			}
		}),
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				secure: false
			}
		}
	}
});
