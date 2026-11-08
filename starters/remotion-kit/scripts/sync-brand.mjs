// Copies the brand logo named in brand/brand.json into public/brand/ so staticFile() can load it.
// brand.json itself is imported directly by src/theme.ts at build time, so it never needs copying.
// Runs automatically before `npm run studio`, `render` and `still`.
import {copyFileSync, existsSync, mkdirSync, readFileSync} from 'node:fs';
import {dirname, extname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const kit = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repo = resolve(kit, '../..');
const brand = JSON.parse(readFileSync(join(repo, 'brand/brand.json'), 'utf8'));
const src = resolve(repo, brand.logo);
const outDir = join(kit, 'public/brand');
mkdirSync(outDir, {recursive: true});
if (!existsSync(src)) {
  console.warn(`sync-brand: logo not found at ${brand.logo}; the end card will show the brand name only.`);
  process.exit(0);
}
const dest = join(outDir, `logo${extname(src)}`);
copyFileSync(src, dest);
console.log(`sync-brand: ${brand.logo} -> public/brand/logo${extname(src)}`);
