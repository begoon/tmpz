import { json } from '@sveltejs/kit';
import { representFace } from '$lib/rankone';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
	const { image } = await request.json();
	const template = await representFace(image);
	return json({ template });
};
