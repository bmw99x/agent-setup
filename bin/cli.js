#!/usr/bin/env node
/**
 * agent-setup installer.
 *
 * Usage:
 *   npx github:bmw99x/agent-setup install [--provider claude,opencode,codex,gemini] [--copy] [--force]
 *   npx github:bmw99x/agent-setup list
 *
 * Default behaviour: detect installed providers, symlink each skill dir into the
 * provider's skill directory, and install AGENTS.md as the provider's global
 * instructions file (skipped if one already exists, unless --force).
 */
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SKILLS_DIR = path.join(ROOT, "skills");
const AGENTS_MD = path.join(ROOT, "AGENTS.md");
const HOME = os.homedir();

const PROVIDERS = {
  claude: {
    detect: path.join(HOME, ".claude"),
    skillsDir: path.join(HOME, ".claude", "skills"),
    instructions: path.join(HOME, ".claude", "CLAUDE.md"),
  },
  opencode: {
    detect: path.join(HOME, ".config", "opencode"),
    skillsDir: path.join(HOME, ".config", "opencode", "skills"),
    instructions: path.join(HOME, ".config", "opencode", "AGENTS.md"),
  },
  codex: {
    detect: path.join(HOME, ".codex"),
    skillsDir: path.join(HOME, ".codex", "skills"),
    instructions: path.join(HOME, ".codex", "AGENTS.md"),
  },
  gemini: {
    detect: path.join(HOME, ".gemini"),
    skillsDir: path.join(HOME, ".gemini", "skills"),
    instructions: path.join(HOME, ".gemini", "GEMINI.md"),
  },
};

function parseArgs(argv) {
  const args = { cmd: argv[0] || "install", providers: null, copy: false, force: false };
  for (let i = 1; i < argv.length; i++) {
    if (argv[i] === "--provider") args.providers = argv[++i].split(",").map((s) => s.trim());
    else if (argv[i] === "--copy") args.copy = true;
    else if (argv[i] === "--force") args.force = true;
    else {
      console.error(`Unknown argument: ${argv[i]}`);
      process.exit(1);
    }
  }
  return args;
}

function skillNames() {
  return fs
    .readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort();
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

function installSkill(name, targetDir, { copy, force }) {
  const src = path.join(SKILLS_DIR, name);
  const dest = path.join(targetDir, name);
  if (fs.existsSync(dest)) {
    const isOurLink = fs.lstatSync(dest).isSymbolicLink() && fs.realpathSync(dest) === fs.realpathSync(src);
    if (!force && !isOurLink) return "skipped (exists)";
    fs.rmSync(dest, { recursive: true, force: true });
  }
  if (copy) {
    copyDir(src, dest);
    return "copied";
  }
  fs.symlinkSync(src, dest, "dir");
  return "linked";
}

function installInstructions(cfg, { force }) {
  if (fs.existsSync(cfg.instructions) && !force) {
    return `skipped (exists — merge ${path.relative(HOME, cfg.instructions)} manually or use --force)`;
  }
  fs.mkdirSync(path.dirname(cfg.instructions), { recursive: true });
  fs.copyFileSync(AGENTS_MD, cfg.instructions);
  return "installed";
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.cmd === "list") {
    console.log("Skills:");
    for (const name of skillNames()) console.log(`  ${name}`);
    return;
  }

  if (args.cmd !== "install") {
    console.error(`Unknown command: ${args.cmd} (expected: install | list)`);
    process.exit(1);
  }

  const wanted = args.providers || Object.keys(PROVIDERS).filter((p) => fs.existsSync(PROVIDERS[p].detect));
  if (wanted.length === 0) {
    console.error("No providers detected. Use --provider claude,opencode,codex,gemini");
    process.exit(1);
  }

  for (const p of wanted) {
    const cfg = PROVIDERS[p];
    if (!cfg) {
      console.error(`Unknown provider: ${p}`);
      process.exit(1);
    }
    console.log(`\n${p}:`);
    fs.mkdirSync(cfg.skillsDir, { recursive: true });
    for (const name of skillNames()) {
      console.log(`  skill ${name}: ${installSkill(name, cfg.skillsDir, args)}`);
    }
    console.log(`  instructions: ${installInstructions(cfg, args)}`);
  }
  console.log("\nDone. Symlinked skills update automatically on git pull; use --copy for standalone copies.");
}

main();
