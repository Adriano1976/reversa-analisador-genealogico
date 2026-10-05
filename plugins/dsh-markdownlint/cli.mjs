//#region cli.mjs
/**
 * Atalho de linha de comando para o mesmo núcleo que a ferramenta `markdown_lint`
 * usa — útil para conferir o plugin sem harness.
 *
 * Uso: `npm run lint -- <diretório> [globo ...]`
 * Ex.: `npm run lint -- .. README.md` ou `npm run lint -- .. docs`
 */

import { runMarkdownlint } from "./lib/lint.js";

const [directory = process.cwd(), ...globs] = process.argv.slice(2);
const result = await runMarkdownlint({ directory, globs: globs.length > 0 ? globs : undefined });
console.log(`exit ${result.exitCode} | ${result.issues.length} problema(s) em ${result.filesWithIssues} arquivo(s)`);
for (const issue of result.issues) {
	const fix = issue.fixable ? " [corrigível]" : "";
	console.log(`${issue.file}:${issue.line}:${issue.column} ${issue.rules[0]} (${issue.severity})${fix} - ${issue.description}`);
}
process.exit(result.exitCode);
//#endregion
