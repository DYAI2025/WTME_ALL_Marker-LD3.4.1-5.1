import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    background: 'extension/src/background.ts',
    'engine.worker': 'extension/src/engine.worker.ts',
  },
  outDir: 'extension/dist',
  format: ['esm'],
  splitting: false,
  clean: true,
  dts: false,
  sourcemap: false,
  treeshake: true,
  minify: false,
});


