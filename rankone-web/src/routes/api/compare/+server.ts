import { json } from '@sveltejs/kit';
import { compareTemplates } from '$lib/rankone';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
	const { type, a, b } = await request.json();
	const similarity = await compareTemplates(type, a, b);
	return json({ similarity });
};
