import { cp, mkdir, rm } from 'node:fs/promises';

await rm('dist', { recursive: true, force: true });
await mkdir('dist', { recursive: true });
await cp('work/stormwater-mvp', 'dist', { recursive: true });
console.log('Stormwater static build copied to dist/');
