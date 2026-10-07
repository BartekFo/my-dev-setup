#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { STATE_DIR, parseArgs, repoRoot, stateDir, walkFiles } from "./lib.mjs";

const UI_LIBRARY_PREFIXES = ["@mantine/", "@mui/", "@chakra-ui/", "antd", "react-bootstrap", "@radix-ui/", "@headlessui/", "primereact", "@nextui-org/", "@heroui/", "@fluentui/", "vuetify", "element-plus", "@angular/material"];

const args = parseArgs(process.argv.slice(2));
const root = repoRoot();
const configFile = path.join(stateDir(root), "config.json");

if (existsSync(configFile) && !args.force) {
  console.log(`config exists: ${configFile} (pass --force to regenerate)`);
  process.exit(0);
}

const packageManager = existsSync(path.join(root, "pnpm-lock.yaml"))
  ? "pnpm"
  : existsSync(path.join(root, "yarn.lock"))
    ? "yarn"
    : "npm";
const exec = { pnpm: "pnpm exec", yarn: "yarn", npm: "npx" }[packageManager];

const packages = walkFiles(root, (file) => path.basename(file) === "package.json")
  .map((file) => ({ dir: path.dirname(file), json: JSON.parse(readFileSync(file, "utf8")) }))
  .flatMap(({ dir, json }) => {
    const deps = { ...json.dependencies, ...json.devDependencies };
    const runner = deps.vitest ? "vitest" : deps.jest ? "jest" : null;
    if (!runner) return [];
    const scripts = json.scripts ?? {};
    const checks = ["tsc:lint", "typecheck", "type-check", "lint", "lint:ci", "format-and-lint"]
      .filter((name) => scripts[name])
      .map((name) => `${packageManager} run ${name}`);
    return [{
      name: json.name ?? path.basename(dir),
      root: path.relative(root, dir) || ".",
      runner,
      testFilePattern: "\\.(test|spec)\\.[cm]?[jt]sx?$",
      runTests: runner === "vitest" ? `${exec} vitest run` : `${exec} jest`,
      checks,
      uiLibraries: Object.keys(deps).filter((dep) => UI_LIBRARY_PREFIXES.some((prefix) => dep.startsWith(prefix))),
      designSystem: ["src/components", "components"].filter((sub) => existsSync(path.join(dir, sub))).map((sub) => path.join(path.relative(root, dir), sub)),
      scopeRoots: ["src/modules", "src/features", "src/components", "src/lib", "src"].filter((sub) => existsSync(path.join(dir, sub))),
    }];
  });

let baseBranch = "main";
try {
  baseBranch = execFileSync("git", ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], { cwd: root, encoding: "utf8" }).trim().replace(/^origin\//, "");
} catch {}

const prTemplate = [".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md"].find((p) => existsSync(path.join(root, p))) ?? null;

const config = {
  baseBranch,
  branchPattern: "test-audit/{scope}",
  prTemplate,
  maxTestsPerBatch: 20,
  minScore: 2,
  scopeDepth: 2,
  packages,
};

mkdirSync(stateDir(root), { recursive: true });
writeFileSync(configFile, `${JSON.stringify(config, null, 2)}\n`);

const commonDir = path.resolve(root, execFileSync("git", ["rev-parse", "--git-common-dir"], { cwd: root, encoding: "utf8" }).trim());
const excludeFile = path.join(commonDir, "info", "exclude");
const excluded = existsSync(excludeFile) ? readFileSync(excludeFile, "utf8") : "";
if (!excluded.split("\n").includes(`${STATE_DIR}/`)) {
  mkdirSync(path.dirname(excludeFile), { recursive: true });
  appendFileSync(excludeFile, `${excluded.endsWith("\n") || excluded === "" ? "" : "\n"}${STATE_DIR}/\n`);
}

console.log(`wrote ${configFile}`);
console.log(JSON.stringify(config, null, 2));
