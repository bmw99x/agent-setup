// Bundles /app/src/main.tsx with esbuild (code splitting on) and reports what the entry screen loads.
import { createRequire } from "node:module";

const require = createRequire("/app/package.json");
const esbuild = require("esbuild");

const result = await esbuild.build({
  absWorkingDir: "/app",
  entryPoints: ["src/main.tsx"],
  bundle: true,
  splitting: true,
  format: "esm",
  outdir: "/tmp/verifier-bundle",
  write: false,
  metafile: true,
  minify: true,
  jsx: "automatic",
  logLevel: "silent",
  define: { "process.env.NODE_ENV": '"production"' },
});

const outputs = result.metafile.outputs;
const entryName = Object.keys(outputs).find((name) => outputs[name].entryPoint === "src/main.tsx");
const eager = new Set();
const queue = [entryName];
while (queue.length) {
  const name = queue.pop();
  if (eager.has(name)) continue;
  eager.add(name);
  for (const imported of outputs[name].imports) {
    if (imported.kind === "import-statement" && outputs[imported.path]) queue.push(imported.path);
  }
}

const eagerInputs = [...eager].flatMap((name) => Object.keys(outputs[name].inputs));
const allInputs = Object.keys(result.metafile.inputs);
const isRecharts = (path) => path.includes("node_modules/recharts/");
const isIcon = (path) => path.includes("node_modules/@mui/icons-material/");
console.log(
  JSON.stringify({
    iconModulesParsed: allInputs.filter(isIcon).length,
    rechartsModulesEager: eagerInputs.filter(isRecharts).length,
    rechartsModulesTotal: allInputs.filter(isRecharts).length,
  }),
);
