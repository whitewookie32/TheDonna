import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter({
			fallback: 'index.html',
			precompress: false,
			strict: false,
			pages: 'build',
			assets: 'build'
		}),
		prerender: {
			handleHttpError: ({ path, referrer, message }) => {
				console.warn(`Prerender warning: ${path} - ${message}`);
				return;
			},
			handleMissingId: 'warn',
			entries: ['*']
		}
	}
};

export default config;
