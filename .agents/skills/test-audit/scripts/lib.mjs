import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

export const STATE_DIR = ".test-audit";
const IGNORED_DIRS = new Set(["node_modules", ".git", ".next", "dist", "build", "coverage", ".turbo", STATE_DIR]);

export function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      args._.push(token);
      continue;
    }
    const key = token.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i++;
    }
  }
  return args;
}

export function fail(message) {
  console.error(`test-audit: ${message}`);
  process.exit(1);
}

export function repoRoot(cwd = process.cwd()) {
  return execFileSync("git", ["rev-parse", "--show-toplevel"], { cwd, encoding: "utf8" }).trim();
}

export function stateDir(root) {
  return path.join(root, STATE_DIR);
}

export function loadConfig(root) {
  const file = path.join(stateDir(root), "config.json");
  if (!existsSync(file)) fail(`no config at ${file}. Run init.mjs first.`);
  return JSON.parse(readFileSync(file, "utf8"));
}

export function selectPackages(config, name) {
  if (!name) return config.packages;
  const match = config.packages.filter((pkg) => pkg.name === name);
  if (match.length === 0) fail(`unknown package "${name}". Known: ${config.packages.map((p) => p.name).join(", ")}`);
  return match;
}

export function loadTypeScript(fromDir) {
  const require = createRequire(path.join(fromDir, "package.json"));
  try {
    return require("typescript");
  } catch {
    fail(`cannot resolve "typescript" from ${fromDir}. Install dependencies in the target repo.`);
  }
}

export function walkFiles(dir, predicate, out = []) {
  for (const entry of readdirSync(dir)) {
    if (IGNORED_DIRS.has(entry)) continue;
    const full = path.join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) walkFiles(full, predicate, out);
    else if (predicate(full)) out.push(full);
  }
  return out;
}

export function isTestFile(file, pkg) {
  return new RegExp(pkg.testFilePattern).test(file);
}

export function createResolver(ts, pkgRoot) {
  const configPath = ts.findConfigFile(pkgRoot, ts.sys.fileExists, "tsconfig.json");
  let options = { moduleResolution: ts.ModuleResolutionKind.Bundler, allowJs: true, jsx: ts.JsxEmit.ReactJSX };
  if (configPath) {
    const read = ts.readConfigFile(configPath, ts.sys.readFile);
    options = ts.parseJsonConfigFileContent(read.config, ts.sys, path.dirname(configPath)).options;
  }
  const cache = new Map();
  return (specifier, fromFile) => {
    const key = `${fromFile}\0${specifier}`;
    if (cache.has(key)) return cache.get(key);
    const resolved = ts.resolveModuleName(specifier, fromFile, options, ts.sys).resolvedModule;
    const file = resolved && !resolved.isExternalLibraryImport && !resolved.resolvedFileName.endsWith(".d.ts")
      ? path.resolve(resolved.resolvedFileName)
      : null;
    cache.set(key, file);
    return file;
  };
}

export function parseSource(ts, file) {
  const text = readFileSync(file, "utf8");
  const kind = file.endsWith(".tsx") || file.endsWith(".jsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  return ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, kind);
}

export function lineOf(sourceFile, node) {
  return sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;
}

export function forEachDescendant(ts, node, visit) {
  ts.forEachChild(node, function walk(child) {
    if (visit(child) === false) return;
    ts.forEachChild(child, walk);
  });
}

export function calleeName(ts, call) {
  let expr = call.expression;
  const parts = [];
  while (expr) {
    if (ts.isIdentifier(expr)) {
      parts.unshift(expr.text);
      break;
    }
    if (ts.isPropertyAccessExpression(expr)) {
      parts.unshift(expr.name.text);
      expr = expr.expression;
    } else if (ts.isCallExpression(expr)) {
      expr = expr.expression;
    } else {
      break;
    }
  }
  return parts.join(".");
}

export function normalize(text) {
  return text.replace(/\s+/g, " ").trim();
}

export function relativeTo(root, file) {
  return path.relative(root, file);
}
