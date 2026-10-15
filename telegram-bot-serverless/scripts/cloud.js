import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const require = createRequire(import.meta.url);
const pkgPath = require.resolve('@tgcloud/cli/package.json');
const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
const bin = typeof pkg.bin === 'string' ? pkg.bin : pkg.bin.tgcloud;
const result = spawnSync(process.execPath, [resolve(dirname(pkgPath), bin), ...process.argv.slice(2)], {
  stdio: 'inherit', env: process.env,
});
if (result.error) console.error('Could not start tgcloud:', result.error.message);
process.exit(result.status ?? 1);
