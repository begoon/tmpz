import { dev } from '$app/environment';

if ('serviceWorker' in navigator) {
	console.log('registering service worker');
	addEventListener('load', function () {
		console.log('loading service worker');
		const status = navigator.serviceWorker.register('/service-worker.js', {
			type: dev ? 'module' : 'classic'
		});
		console.log('status', status);
	});
}
