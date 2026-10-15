import { globSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

// Telegram runs these ES modules directly. Syntax validation is the build step;
// sdk imports are provided by the platform and are exercised locally in tests.
const files = [...globSync(['tgcloud/**/*.js', 'scripts/**/*.js', 'tests/**/*.js'])].sort();
for (const file of files) {
  const result = spawnSync(process.execPath, ['--check', file], { stdio: 'inherit' });
  if (result.error || result.status !== 0) process.exit(result.status || 1);
}
console.log(`Validated ${files.length} JavaScript files. Ready for source deployment.`);
