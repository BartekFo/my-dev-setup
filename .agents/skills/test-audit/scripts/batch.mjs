#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fail, loadConfig, parseArgs, relativeTo, repoRoot, stateDir } from "./lib.mjs";

const args = parseArgs(process.argv.slice(2));
const root = repoRoot();
const config = loadConfig(root);
const candidatesFile = path.join(stateDir(root), "candidates.json");
if (!existsSync(candidatesFile)) fail("no candidates.json. Run scan.mjs first.");
const scan = JSON.parse(readFileSync(candidatesFile, "utf8"));
const minScore = Number(args["min-score"] ?? config.minScore);
const maxTests = Number(args.max ?? config.maxTestsPerBatch);
const depth = Number(args.depth ?? config.scopeDepth ?? 1);
const scriptDir = path.dirname(new URL(import.meta.url).pathname);

const batches = [];
for (const pkg of scan.packages) {
  const pkgConfig = config.packages.find((p) => p.name === pkg.name);
  const scopes = new Map();
  for (const file of pkg.files) {
    const candidates = file.tests.filter((t) => t.score >= minScore);
    const review = file.tests.filter((t) => t.score > 0 && t.score < minScore);
    const uiMocks = file.mocks.filter((m) => ["ui-library", "design-system", "component"].includes(m.category));
    if (candidates.length === 0 && uiMocks.length === 0) continue;
    const scope = scopeOf(path.relative(pkg.root, file.file), pkgConfig.scopeRoots);
    const list = scopes.get(scope) ?? [];
    list.push({ ...file, candidates, review, uiMocks });
    scopes.set(scope, list);
  }
  for (const [scope, files] of scopes) {
    let current = null;
    for (const file of files.sort((a, b) => a.file.localeCompare(b.file))) {
      if (!current || current.size + file.candidates.length > maxTests) {
        current = { package: pkg.name, scope, files: [], size: 0 };
        batches.push(current);
      }
      current.files.push(file);
      current.size += file.candidates.length;
    }
  }
}

batches.sort((a, b) => b.size - a.size);
const outDir = path.join(stateDir(root), "batches");
rmSync(outDir, { recursive: true, force: true });
mkdirSync(outDir, { recursive: true });
const index = batches.map((batch, i) => {
  const id = `${String(i + 1).padStart(2, "0")}-${batch.scope.replace(/[^A-Za-z0-9]+/g, "-")}`;
  writeFileSync(path.join(outDir, `${id}.md`), worksheet(id, batch));
  return { id, package: batch.package, scope: batch.scope, candidates: batch.size, files: batch.files.length };
});
writeFileSync(path.join(outDir, "index.json"), `${JSON.stringify(index, null, 2)}\n`);

console.log("batch                                            pkg        cand files");
for (const b of index) console.log(`${b.id.padEnd(48)} ${b.package.padEnd(10)} ${String(b.candidates).padStart(4)} ${String(b.files).padStart(5)}`);
console.log(`\nwrote ${index.length} worksheets to ${relativeTo(root, outDir)}`);

function scopeOf(relFile, scopeRoots) {
  const parts = relFile.split(path.sep);
  const rootMatch = [...scopeRoots].sort((a, b) => b.length - a.length).find((r) => relFile.startsWith(`${r}${path.sep}`));
  const base = rootMatch ? rootMatch.split("/").length : 0;
  return parts.slice(Math.max(0, base - 1), base + depth).join("/");
}

function worksheet(id, batch) {
  const owners = [...new Set(batch.files.map((f) => f.owner).filter(Boolean))];
  const lines = [
    `# ${id}`,
    "",
    `package \`${batch.package}\` · scope \`${batch.scope}\` · ${batch.size} candidates in ${batch.files.length} files`,
    "",
    "## Mutation proof",
    "",
    ...owners.map((owner) => `- \`node ${path.join(scriptDir, "mutate.mjs")} --package ${batch.package} --owner ${owner}\``),
    "",
    "## Files",
  ];
  for (const file of batch.files) {
    lines.push("", `### \`${file.file}\``, "", `owner: ${file.owner ? `\`${file.owner}\`` : "unknown"}`);
    if (file.uiMocks.length > 0) lines.push(`mocks UI layer: ${file.uiMocks.map((m) => `\`${m.specifier}\` (${m.category})`).join(", ")}`);
    for (const test of file.candidates) {
      lines.push(
        "",
        `#### L${test.line}–${test.endLine} · score ${test.score} · ${test.fullName}`,
        "",
        ...test.flags.map((f) => `- **${f.id}**: ${f.evidence.map((e) => `\`${e.replace(/`/g, "'")}\``).join("; ")}`),
        "",
        "| field | value |",
        "| --- | --- |",
        "| verdict (delete · rewrite · extract-logic · keep) | |",
        "| failure it can detect | |",
        "| stronger owner-boundary proof | |",
        "| mutation evidence | |",
        "| production seam unlocked | |",
        "| history / why it exists | |",
      );
    }
    if (file.review.length > 0) {
      lines.push("", "review only (score below threshold):");
      for (const test of file.review) lines.push(`- L${test.line} ${test.fullName} — ${test.flags.map((f) => f.id).join(", ")}`);
    }
  }
  return `${lines.join("\n")}\n`;
}
