#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fail, loadConfig, parseArgs, relativeTo, repoRoot, selectPackages, stateDir } from "./lib.mjs";

const args = parseArgs(process.argv.slice(2));
const root = repoRoot();
const config = loadConfig(root);
const candidatesFile = path.join(stateDir(root), "candidates.json");
if (!existsSync(candidatesFile)) fail("no candidates.json. Run scan.mjs first.");
const scan = JSON.parse(readFileSync(candidatesFile, "utf8"));
if (!existsSync(path.join(root, "node_modules", ".bin", "knip"))) fail("knip is not installed in this repo. Test-only export detection needs `knip --production`.");

const report = [];
for (const pkg of selectPackages(config, args.package)) {
  const run = spawnSync("node_modules/.bin/knip", ["--production", "--include", "exports,types", "--reporter", "json", ...(pkg.root === "." ? [] : ["-W", pkg.root])], { cwd: root, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  const json = run.stdout.trim().startsWith("{") ? JSON.parse(run.stdout) : null;
  if (!json) fail(`knip produced no JSON for ${pkg.name}:\n${run.stderr.slice(0, 2000)}`);
  const testImports = scan.packages.find((p) => p.name === pkg.name)?.files.flatMap((f) => f.imports.map((imp) => ({ ...imp, test: f.file }))) ?? [];
  for (const issue of json.issues ?? []) {
    for (const item of [...(issue.exports ?? []), ...(issue.types ?? [])]) {
      const users = testImports.filter((imp) => imp.resolved === issue.file && imp.names.includes(item.name)).map((imp) => imp.test);
      if (users.length > 0) report.push({ package: pkg.name, file: issue.file, name: item.name, line: item.line, tests: [...new Set(users)] });
    }
  }
}

const outFile = path.join(stateDir(root), "seams.json");
writeFileSync(outFile, `${JSON.stringify(report, null, 2)}\n`);
console.log("exports with no production importer, imported by tests:");
for (const seam of report) console.log(`  ${seam.file}:${seam.line} ${seam.name}  ← ${seam.tests.map((t) => path.basename(t)).join(", ")}`);
console.log(`\n${report.length} test-only seams · wrote ${relativeTo(root, outFile)}`);
