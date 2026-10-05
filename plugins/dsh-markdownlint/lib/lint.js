//#region lib/lint.js
/**
 * Núcleo do plugin: roda o `markdownlint-cli2` **em processo** e devolve o
 * resultado em forma estruturada.
 *
 * O `main` do markdownlint-cli2 entrega o relatório a formatadores de saída e
 * escreve o resto (banner, progresso, resumo) pelos loggers. Aqui o formatador
 * padrão é substituído por um capturador — via
 * `optionsOverride.outputFormatters`, que o CLI2 aplica depois de qualquer
 * arquivo de configuração — de modo que a ferramenta devolva dados, e não
 * texto de console para o modelo.
 *
 * Nada aqui conhece o harness: este módulo é importável e testável sozinho.
 *
 * @module dsh-markdownlint/lint
 */

import { isAbsolute, resolve } from "node:path";
import { main } from "markdownlint-cli2";

/**
 * Padrões de inclusão padrão: todo Markdown do workspace.
 */
export const DEFAULT_GLOBS = ["**/*.md"];

/**
 * Padrões de exclusão **sempre** aplicados, mesmo quando o chamador passa os
 * próprios globos: árvores que nunca são documentação autoral e que, lintadas,
 * devolveriam milhares de problemas de terceiros. O CLI2 aceita padrões negados
 * com `!` ou `#`.
 */
export const DEFAULT_IGNORES = [
	"!**/node_modules/**",
	"!**/.git/**",
	"!**/.venv/**",
	"!**/venv/**"
];

/** Uma entrada de `LintError` do markdownlint, achatada para o payload da ferramenta. */
const toIssue = (result) => ({
	file: result.fileName,
	line: Number.isInteger(result.lineNumber) && result.lineNumber > 0 ? result.lineNumber : 1,
	column: Array.isArray(result.errorRange) && result.errorRange.length > 0 ? result.errorRange[0] : 1,
	rules: Array.isArray(result.ruleNames) ? [...result.ruleNames] : [],
	severity: result.severity === "warning" ? "warning" : "error",
	description:
		typeof result.ruleDescription === "string"
			? `${result.ruleDescription}${result.errorDetail ? ` (${result.errorDetail})` : ""}`
			: String(result.errorDetail ?? "problema sem descrição"),
	fixable: Boolean(result.fixInfo)
});

/** Ordena por arquivo, linha, coluna e primeira regra — a mesma leitura do CLI. */
const compareIssues = (a, b) =>
	a.file.localeCompare(b.file) ||
	a.line - b.line ||
	a.column - b.column ||
	(a.rules[0] ?? "").localeCompare(b.rules[0] ?? "");

/**
 * Executa o markdownlint-cli2 em `directory` e devolve o resultado capturado.
 *
 * A configuração é descoberta exatamente como no CLI: `.markdownlint-cli2.jsonc`
 * / `.yaml` / `.mjs` e `.markdownlint.jsonc` / `.yaml` / `.mjs` são procurados a
 * partir do diretório-base e herdados pelas subpastas, com `overrides` e
 * `customRules` valendo.
 *
 * @param {object} options - opções da execução.
 * @param {string} options.directory - diretório-base (onde o CLI seria chamado).
 * @param {string[]} [options.globs] - padrões de inclusão; padrão {@link DEFAULT_GLOBS}.
 *   {@link DEFAULT_IGNORES} é anexado de qualquer forma.
 * @param {boolean} [options.fix] - aplica `--fix` (reescreve os arquivos, sem backup).
 * @param {string} [options.config] - caminho de arquivo de configuração (`--config`).
 * @returns {Promise<{exitCode: number, directory: string, issues: object[], filesWithIssues: number, fixableCount: number, log: string}>}
 *   o resultado: `exitCode` 0 sem erros, 1 com erros, 2 quando o CLI não chegou a
 *   lintar (problema de configuração ou nenhum globo); `issues` traz uma entrada
 *   por problema relatado; `log` preserva banner, progresso e resumo do CLI.
 */
export async function runMarkdownlint(options) {
	const { directory, globs = DEFAULT_GLOBS, fix = false, config } = options;
	/** @type {string[]} */
	const messages = [];
	/** @type {string[]} */
	const problems = [];
	/** @type {object[]} */
	let captured = [];
	// Formatador de saída próprio: recebe os resultados e não escreve nada.
	const capture = (formatterOptions) => {
		captured = captured.concat(formatterOptions.results);
	};
	const argv = [...globs, ...DEFAULT_IGNORES];
	if (config !== undefined) {
		argv.push("--config", config);
	}
	if (fix) {
		argv.push("--fix");
	}
	const exitCode = await main({
		directory,
		argv,
		optionsOverride: { outputFormatters: [[capture]] },
		logMessage: (message) => messages.push(message),
		logError: (message) => problems.push(message)
	});
	const issues = captured.map(toIssue).sort(compareIssues);
	return {
		exitCode,
		directory,
		issues,
		filesWithIssues: new Set(issues.map((issue) => issue.file)).size,
		fixableCount: issues.filter((issue) => issue.fixable).length,
		log: [...messages, ...problems].join("\n")
	};
}

/**
 * Resolve o diretório de trabalho: um caminho relativo é resolvido contra o
 * workspace da sessão, como em `pwsh`/`read`/`write`.
 *
 * @param {string | undefined} workdir - `workdir` pedido pelo modelo, se houver.
 * @param {string | undefined} headerCwd - `cwd` do cabeçalho da sessão.
 * @returns {string | undefined} o diretório absoluto, ou `undefined` quando nem o
 *   pedido nem a sessão oferecem um.
 */
export function resolveDirectory(workdir, headerCwd) {
	if (workdir === undefined) {
		return headerCwd;
	}
	if (headerCwd !== undefined && !isAbsolute(workdir)) {
		return resolve(headerCwd, workdir);
	}
	return workdir;
}
//#endregion
