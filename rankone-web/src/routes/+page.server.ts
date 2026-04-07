import { versionStrings } from '$lib/rankone';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	const versions = await versionStrings();
	return { versions };
};
