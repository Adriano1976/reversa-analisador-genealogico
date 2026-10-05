//#region lib/index.js
/**
 * Plugin host do harness: registra a ferramenta `markdown_lint`, apoiada no
 * `markdownlint-cli2` (https://github.com/DavidAnson/markdownlint-cli2).
 *
 * O plugin não fala com o executor de shell nem com o sistema de arquivos do
 * harness: o lint roda em processo, sobre o diretório do workspace da sessão, e
 * a configuração do projeto é descoberta pelo próprio CLI. O resultado volta
 * estruturado (uma entrada por problema) para o modelo decidir o que fazer.
 *
 * @module dsh-markdownlint
 */

import { defineTool } from "@deepseek-ai/dsh-tools";
import { DEFAULT_GLOBS, DEFAULT_IGNORES, resolveDirectory, runMarkdownlint } from "./lint.js";

/** Nome do plugin para o loader do Cordis. */
export const name = "markdownlint";
/** Este plugin só precisa do registro de ferramentas. */
export const inject = ["tools"];

/** Quantos problemas o relatório textual lista antes de resumir o resto. */
const RENDER_LIMIT = 100;

const DESCRIPTION = [
	"Linta Markdown/CommonMark com o `markdownlint-cli2` e devolve os problemas em forma estruturada (arquivo, linha, coluna, regras, descrição e se é corrigível).",
	"A configuração é descoberta como no CLI — `.markdownlint-cli2.jsonc|yaml|cjs|mjs` e `.markdownlint.jsonc|json|yaml|yml|cjs|mjs`, com herança por diretório, `overrides` e `customRules` — então não é preciso passar regras.",
	`O padrão é \`${DEFAULT_GLOBS.join(" ")}\`; passe \`globs\` para restringir (ex.: \`["docs/**/*.md"]\`) e use \`!padrão\` para excluir mais.`,
	`\`${DEFAULT_IGNORES.join(" ")}\` são excluídos sempre, mesmo com \`globs\` próprios.`,
	"`fix: true` reescreve os arquivos no lugar (`--fix`, sem backup) e só deve ser usado quando o usuário pedir a correção.",
	"Exit code 0 = nenhum erro, 1 = erros encontrados, 2 = o CLI não chegou a lintar (configuração inválida ou nenhum globo).",
	"Use quando precisar validar ou corrigir a forma de arquivos Markdown do projeto (README, specs, docs)."
].join(" ");

/**
 * Relatório textual devolvido ao modelo: cabeçalho de contagem, uma linha por
 * problema e o rodapé de truncamento quando a lista passa de {@link RENDER_LIMIT}.
 *
 * @param {object} value - valor canônico validado da ferramenta.
 * @returns {string} o relatório em texto.
 */
function renderReport(value) {
	const scope = value.fixed ? "markdownlint --fix" : "markdownlint";
	if (value.exitCode === 2) {
		return `${scope}: o lint não foi concluído (exit 2) em ${value.directory}. Confira o arquivo de configuração e os globos pedidos.\n${value.log}`.trim();
	}
	if (value.issueCount === 0) {
		return `${scope}: nenhum problema em ${value.directory} (exit 0).`;
	}
	const shown = value.issues.slice(0, RENDER_LIMIT).map((issue) => {
		const rules = issue.rules.join("/");
		const fix = issue.fixable ? " [corrigível]" : "";
		return `- ${issue.file}:${issue.line}:${issue.column} ${rules} (${issue.severity})${fix}: ${issue.description}`;
	});
	if (value.issues.length > shown.length) {
		shown.push(`- ... e mais ${value.issues.length - shown.length} problema(s) na lista estruturada.`);
	}
	const head = `${scope}: ${value.issueCount} problema(s) em ${value.filesWithIssues} arquivo(s)${value.fixableCount > 0 ? ` (${value.fixableCount} corrigível(is) automaticamente)` : ""}.`;
	const tail = value.fixed ? "Correções aplicadas foram reescritas nos arquivos." : "Rode de novo com fix: true para aplicar as correções possíveis.";
	return [head, ...shown, tail].join("\n");
}

/**
 * Registra a ferramenta `markdown_lint` no registro de ferramentas do harness.
 *
 * @param {object} ctx - contexto do plugin, com o registro `tools`.
 */
export function apply(ctx) {
	ctx.tools.register(defineTool({
		name: "markdown_lint",
		description: DESCRIPTION,
		parameters: {
			globs: {
				type: "array",
				items: { type: "string" },
				description: `Padrões a lintar, na sintaxe do globby. Padrão: ${DEFAULT_GLOBS.join(" ")}. Um padrão iniciado por "!" (ou "#") exclui arquivos; ${DEFAULT_IGNORES.join(" ")} valem sempre.`
			},
			fix: {
				type: "boolean",
				description: "Aplica as correções automáticas e reescreve os arquivos no lugar (--fix, sem backup e fora do sandbox de escrita do harness). Só use quando o usuário pedir para corrigir."
			},
			config: {
				type: "string",
				description: "Caminho de um arquivo de configuração do markdownlint(-cli2) a usar como base (--config). Opcional: a configuração do projeto é descoberta sozinha."
			},
			workdir: {
				type: "string",
				description: "Diretório-base do lint. Padrão: o workspace da sessão; um caminho relativo é resolvido contra ele."
			}
		},
		output: {
			schema: {
				type: "object",
				additionalProperties: false,
				properties: {
					ok: {
						type: "boolean",
						required: true,
						description: "true quando não há nenhum problema de severidade error."
					},
					exitCode: {
						type: "integer",
						required: true,
						description: "0 sem erros, 1 com erros, 2 quando o CLI não lintou."
					},
					directory: {
						type: "string",
						required: true,
						description: "Diretório-base em que o lint rodou."
					},
					filesWithIssues: {
						type: "integer",
						required: true
					},
					issueCount: {
						type: "integer",
						required: true
					},
					fixableCount: {
						type: "integer",
						required: true,
						description: "Quantos problemas têm correção automática disponível."
					},
					fixed: {
						type: "boolean",
						required: true,
						description: "Se esta execução rodou com --fix."
					},
					issues: {
						type: "array",
						required: true,
						items: {
							type: "object",
							additionalProperties: false,
							properties: {
								file: {
									type: "string",
									required: true,
									description: "Caminho relativo ao diretório-base."
								},
								line: {
									type: "integer",
									required: true
								},
								column: {
									type: "integer",
									required: true
								},
								rules: {
									type: "array",
									required: true,
									items: { type: "string" }
								},
								severity: {
									type: "string",
									required: true,
									enum: ["error", "warning"]
								},
								description: {
									type: "string",
									required: true
								},
								fixable: {
									type: "boolean",
									required: true
								}
							}
						}
					},
					log: {
						type: "string",
						required: true,
						description: "Banner, progresso e resumo escritos pelo CLI (stdout + stderr)."
					}
				}
			},
			render: (_args, value) => [{ type: "text", text: renderReport(value) }]
		},
		async execute(args, exec) {
			const directory = resolveDirectory(args.workdir, exec.agent?.session.header.cwd);
			if (directory === undefined) {
				throw new Error("markdown_lint: nenhum diretório de trabalho disponível nesta sessão; passe `workdir`");
			}
			if (exec.signal?.aborted) {
				const error = new Error("markdown_lint: chamada cancelada");
				error.name = "AbortError";
				throw error;
			}
			const result = await runMarkdownlint({
				directory,
				globs: args.globs,
				fix: args.fix === true,
				config: args.config
			});
			return {
				ok: result.issues.every((issue) => issue.severity !== "error"),
				exitCode: result.exitCode,
				directory: result.directory,
				filesWithIssues: result.filesWithIssues,
				issueCount: result.issues.length,
				fixableCount: result.fixableCount,
				fixed: args.fix === true,
				issues: result.issues,
				log: result.log
			};
		},
		presentCall: (args) => ({
			card: "generic",
			title: `markdownlint ${args.fix === true ? "--fix " : ""}${(args.globs ?? DEFAULT_GLOBS).join(" ")}`,
			kind: "execute",
			rawInput: args
		}),
		presentResult: (_args, result) => {
			const block = result.content.length === 1 ? result.content[0] : undefined;
			if (block === undefined || block.type !== "text") {
				return undefined;
			}
			return {
				card: "generic",
				content: [{ type: "text", text: `\`\`\`\n${block.text.replace(/\n+$/, "")}\n\`\`\`` }]
			};
		}
	}));
}
//#endregion
