//#region smoke.mjs
/**
 * Teste de fumaça do plugin, sem harness: prova que o núcleo de lint encontra
 * problemas, que o modo `fix` corrige o que é corrigível e que a definição da
 * ferramenta compila (`defineTool` valida os esquemas na hora de definir).
 *
 * Uso: `npm run smoke` (precisa de `npm install` e, para a última checagem,
 * de `npm run link-host`).
 */

import { cp, mkdir, readFile, rm } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { runMarkdownlint } from "./lib/lint.js";

const here = dirname(fileURLToPath(import.meta.url));
const sandbox = join(here, ".smoke");
const fixture = join(here, "fixtures", "quebrado.md");
const checks = [];
let failed = 0;

/** Registra o resultado de uma checagem. */
const check = (label, condition, detail = "") => {
	checks.push(`${condition ? "ok  " : "FALHA"} ${label}${detail ? ` — ${detail}` : ""}`);
	if (!condition) {
		failed++;
	}
};

await rm(sandbox, { recursive: true, force: true });
await mkdir(sandbox, { recursive: true });
await cp(fixture, join(sandbox, "quebrado.md"));

// 1) Lint puro: o fixture tem violações conhecidas (MD009, MD012, MD022, MD030, MD032).
const first = await runMarkdownlint({ directory: sandbox, globs: ["**/*.md"] });
const rules = new Set(first.issues.flatMap((issue) => issue.rules.map((rule) => rule.split("/")[0])));
check("lint acha as violações do fixture", first.issues.length >= 4, `${first.issues.length} problema(s)`);
check("lint acha MD009 (espaços no fim da linha)", rules.has("MD009"), [...rules].sort().join(", "));
check("todo problema traz arquivo, linha e regra", first.issues.every((issue) => issue.file && issue.line > 0 && issue.rules.length > 0));
check("exit code 1 quando há erros", first.exitCode === 1, `exit ${first.exitCode}`);

// 2) Modo fix: as violações do fixture são todas corrigíveis.
const fixed = await runMarkdownlint({ directory: sandbox, globs: ["**/*.md"], fix: true });
check("fix deixa o arquivo limpo", fixed.issues.length === 0, `restaram ${fixed.issues.length}`);
const content = await readFile(join(sandbox, "quebrado.md"), "utf8");
check("fix reescreveu o arquivo (sem espaços no fim de linha)", content.split(/\r?\n/u).every((line) => line === line.replace(/\s+$/u, "")));

// 3) Idempotência: rodar de novo não acha nada.
const again = await runMarkdownlint({ directory: sandbox, globs: ["**/*.md"] });
check("segunda passada limpa", again.issues.length === 0 && again.exitCode === 0, `exit ${again.exitCode}`);

// 4) A definição da ferramenta compila e renderiza.
try {
	const { apply } = await import("./lib/index.js");
	let registered = null;
	apply({ tools: { register: (definition) => { registered = definition; } } });
	check("a ferramenta markdown_lint foi definida", registered?.name === "markdown_lint", registered?.name);
	const rendered = registered.output.render({}, {
		ok: false,
		exitCode: 1,
		directory: sandbox,
		filesWithIssues: first.filesWithIssues,
		issueCount: first.issues.length,
		fixableCount: first.fixableCount,
		fixed: false,
		issues: first.issues,
		log: first.log
	});
	check("o render devolve texto", rendered?.[0]?.type === "text" && rendered[0].text.includes("MD009"));
} catch (error) {
	if (error?.code === "ERR_MODULE_NOT_FOUND") {
		checks.push("pule a checagem da definição da ferramenta: rode `npm run link-host` primeiro");
	} else {
		throw error;
	}
}

await rm(sandbox, { recursive: true, force: true });
console.log(checks.join("\n"));
console.log(failed === 0 ? "\nsmoke: tudo certo" : `\nsmoke: ${failed} checagem(ns) falharam`);
process.exit(failed === 0 ? 0 : 1);
//#endregion
