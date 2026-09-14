import type { PageServerLoad } from './$types';

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export const load: PageServerLoad = async () => {
	const serverTime = new Date().toLocaleTimeString(undefined, { hour12: false });

	return {
		serverTime,
		products: ['Apples', 'Bread', 'Coffee', 'Dates'],
		chart: [12, 30, 22, 45, 38, 60, 52, 71, 64, 80],
		// A top-level promise streams to the client instead of blocking the initial HTML.
		stats: sleep(1500).then(() => ({
			visitors: 48213 + Math.floor(Math.random() * 100),
			uptime: '99.98%'
		}))
	};
};
