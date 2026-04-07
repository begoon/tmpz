import { json } from '@sveltejs/kit';
import { representFingerprint } from '$lib/rankone';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
	const { image } = await request.json();
	const template = await representFingerprint(image);
	return json({ template });
};
