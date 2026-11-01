//#region lib/index.js
/**
 * Plugin `fala` do harness: lê em voz alta o desfecho de cada turno concluído
 * na sessão em que o usuário chamou `/fala-on`, e fica muda em todas as outras.
 *
 * É o porte do mod "fala" do Claude Code (edge-tts + ffplay, voz
 * `pt-BR-ThalitaMultilingualNeural`) para os pontos de extensão nativos do
 * DeepSeek Harness: comandos de host (`ctx.commands.register`) para ligar e
 * desligar por sessão, e o firehose `session/event` para saber quando um turno
 * terminou com resposta.
 *
 * Regras herdadas do mod:
 *
 * - a voz começa DESLIGADA em toda sessão; só a sessão em que `/fala-on` foi
 *   chamado fala, então várias sessões abertas não falam ao mesmo tempo;
 * - cada resposta só toca depois que a anterior terminou (fila);
 * - nada é falado em turno abortado, com erro, bloqueado ou sem texto; o
 *   desfecho falado é o do turno `completed`;
 * - o Markdown é reduzido a prosa antes de virar áudio.
 *
 * @module dsh-fala
 */

import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

/** Voz do edge-tts, a mesma do mod original. */
const VOZ_PADRAO = "pt-BR-ThalitaMultilingualNeural";
/** Texto acima disso é cortado: o áudio de um turno gigante não vale a espera. */
const LIMITE_PADRAO = 4000;
/** Teto para sintetizar uma fala (a síntese depende da rede). */
const TIMEOUT_SINTESE_MS = 300_000;
/** Teto para tocar a fala sintetizada. */
const TIMEOUT_TOQUE_MS = 600_000;
/** Marca no processo do ffplay de que a parada foi pedida por `/fala-off`. */
const PARADA = Symbol("parada");

/** Nome do plugin para o loader do Cordis. */
export const name = "fala";
/** Este plugin só precisa do registro de comandos de host. */
export const inject = ["commands"];

/** Sessões com a voz ligada (`/fala-on`), por id de sessão. */
const ligadas = new Set();
/**
 * Último texto de assistente de cada sessão, com o turno a que pertence.
 * Servido no `turn/end` para falar exatamente o desfecho do turno.
 * @type {Map<string, { turn: number, texto: string }>}
 */
const ultimos = new Map();
/** Fila: cada resposta só toca depois que a anterior terminou. */
let fila = Promise.resolve();
/**
 * Geração da voz: `/fala-off` incrementa e o que estava na fila é descartado.
 * Sem isso, desligar a voz ainda tocaria as respostas já enfileiradas.
 */
let geracao = 0;
/** Interrompe o áudio em curso, quando há um tocando. */
let pararAtual = null;

/**
 * Reduz Markdown a algo que valha a pena ouvir: sem cercas de código, sem
 * marcação, sem links vazios e com a pontuação colada no texto.
 *
 * @param {string} texto - texto cru da mensagem.
 * @returns {string} prosa falável.
 */
function limpar(texto) {
	return texto
		.replace(/```[\s\S]*?```/g, " ")
		.replace(/~~~[\s\S]*?~~~/g, " ")
		.replace(/`([^`]*)`/g, "$1")
		.replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
		.replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
		.replace(/^[ \t]*[#>]+[ \t]*/gm, "")
		.replace(/^[ \t]*[-*+][ \t]+/gm, "")
		.replace(/[*_~]{1,3}/g, "")
		.replace(/[ \t]+/g, " ")
		.replace(/\n{2,}/g, ". ")
		.replace(/\n/g, " ")
		.replace(/\s+([.,;:!?])/g, "$1")
		.replace(/\.(\s*\.)+/g, ".")
		.replace(/\s{2,}/g, " ")
		.trim();
}

/**
 * Extrai o texto visível de uma mensagem de assistente. Reasonings e blocos
 * de ferramenta ficam mudos: só a prosa que o usuário vê vira áudio.
 *
 * @param {object} mensagem - mensagem do evento `assistant/message`.
 * @returns {string} o texto das partes faláveis, unido por quebra de linha.
 */
function textoDaMensagem(mensagem) {
	if (mensagem === null || typeof mensagem !== "object" || !Array.isArray(mensagem.content)) return "";
	const partes = [];
	for (const bloco of mensagem.content) {
		if (bloco !== null && typeof bloco === "object" && bloco.type === "text" && typeof bloco.text === "string") {
			partes.push(bloco.text);
		}
	}
	return partes.join("\n");
}

/**
 * Roda um processo e resolve quando ele sai com código 0.
 *
 * @param {string} arquivo - executável a iniciar.
 * @param {string[]} args - argumentos, sem shell.
 * @param {number} timeoutMs - teto de vida do processo.
 * @param {(filho: import("node:child_process").ChildProcess) => void} [aoIniciar] - recebe o processo assim que ele nasce.
 * @returns {Promise<void>} quando o processo termina bem.
 */
function rodar(arquivo, args, timeoutMs, aoIniciar) {
	return new Promise((resolve, reject) => {
		const filho = spawn(arquivo, args, { windowsHide: true, stdio: ["ignore", "ignore", "pipe"] });
		aoIniciar?.(filho);
		let erro = "";
		const alarme = setTimeout(() => {
			filho.kill();
			reject(new Error(`${arquivo}: tempo esgotado depois de ${timeoutMs}ms`));
		}, timeoutMs);
		filho.stderr.on("data", (pedaco) => {
			erro = `${erro}${pedaco}`.slice(-4096);
		});
		filho.on("error", (falha) => {
			clearTimeout(alarme);
			reject(falha);
		});
		filho.on("close", (codigo) => {
			clearTimeout(alarme);
			if (codigo === 0 || filho[PARADA] === true) {
				resolve();
				return;
			}
			reject(new Error(`${arquivo} saiu com código ${codigo}: ${erro.trim()}`));
		});
	});
}

/**
 * Sintetiza um texto em MP3 com o edge-tts.
 *
 * O comando `edge-tts` do PATH é a primeira tentativa; quando ele não existe,
 * o mesmo pacote é chamado como módulo do Python. Só a ausência do executável
 * (`ENOENT`) faz cair para a tentativa seguinte — uma falha de rede ou de voz
 * é reportada como está, sem máscara.
 *
 * @param {string} texto - texto já limpo.
 * @param {{ voz: string, pasta: string }} opcoes - voz e pasta de trabalho.
 * @returns {Promise<string>} caminho do MP3 gerado.
 */
async function sintetizar(texto, opcoes) {
	const entrada = join(opcoes.pasta, "fala.txt");
	const saida = join(opcoes.pasta, "fala.mp3");
	await writeFile(entrada, texto, "utf8");
	const tentativas = [
		["edge-tts", ["--voice", opcoes.voz, "--file", entrada, "--write-media", saida]],
		["python", ["-m", "edge_tts", "--voice", opcoes.voz, "--file", entrada, "--write-media", saida]]
	];
	let falha;
	for (const [arquivo, args] of tentativas) {
		try {
			await rodar(arquivo, args, TIMEOUT_SINTESE_MS);
			return saida;
		} catch (erro) {
			falha = erro;
			if (erro?.code !== "ENOENT") break;
		}
	}
	throw falha;
}

/**
 * Fala um texto: sintetiza com o edge-tts e toca com o ffplay.
 *
 * @param {object} ctx - contexto do plugin, para log.
 * @param {string} texto - texto já limpo.
 * @param {{ voz: string, dryRun: boolean }} opcoes - voz e modo de ensaio.
 * @param {number} minhaGeracao - geração da voz no momento em que esta fala entrou na fila.
 * @returns {Promise<void>} quando o áudio termina (ou o ensaio registra a fala).
 */
async function falar(ctx, texto, opcoes, minhaGeracao) {
	if (minhaGeracao !== geracao) return;
	if (opcoes.dryRun) {
		ctx.logger.info(`fala (ensaio): ${texto}`);
		return;
	}
	const pasta = await mkdtemp(join(tmpdir(), "dsh-fala-"));
	try {
		const audio = await sintetizar(texto, { voz: opcoes.voz, pasta });
		if (minhaGeracao !== geracao) return;
		await rodar("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet", audio], TIMEOUT_TOQUE_MS, (filho) => {
			pararAtual = () => {
				filho[PARADA] = true;
				try {
					filho.kill();
				} catch {}
			};
		});
	} finally {
		pararAtual = null;
		await rm(pasta, { recursive: true, force: true }).catch(() => {});
	}
}

/**
 * Registra `/fala-on` e `/fala-off` e passa a falar o desfecho dos turnos das
 * sessões ligadas.
 *
 * @param {object} ctx - contexto do plugin, com o registro `commands`.
 * @param {{ voz?: string, limite?: number, dryRun?: boolean } | undefined} config - ajustes opcionais.
 */
export function apply(ctx, config) {
	const voz = config?.voz ?? VOZ_PADRAO;
	const limite = config?.limite ?? LIMITE_PADRAO;
	const opcoes = { voz, dryRun: config?.dryRun === true };

	ctx.commands.register({
		name: "fala-on",
		description: "Liga a leitura em voz alta nesta sessão (voz Thalita, edge-tts)",
		handler: ({ agent }) => {
			ligadas.add(agent.session.id);
			return { kind: "success", text: "Voz ligada nesta sessão." };
		}
	});

	ctx.commands.register({
		name: "fala-off",
		description: "Desliga a leitura em voz alta nesta sessão",
		handler: ({ agent }) => {
			ligadas.delete(agent.session.id);
			// Cala agora: descarta a fila e interrompe o áudio em curso.
			geracao += 1;
			pararAtual?.();
			pararAtual = null;
			return { kind: "success", text: "Voz desligada nesta sessão." };
		}
	});

	ctx.on("session/event", (session, evento) => {
		if (evento.type === "assistant/message") {
			const texto = textoDaMensagem(evento.data.message);
			if (texto !== "") ultimos.set(session.id, { turn: evento.data.turn, texto });
			return;
		}
		if (evento.type !== "turn/end") return;
		if (evento.data.reason.kind !== "completed") return;
		if (!ligadas.has(session.id)) return;

		const guardado = ultimos.get(session.id);
		ultimos.delete(session.id);
		if (guardado === undefined || guardado.turn !== evento.data.turn) return;

		let texto = limpar(guardado.texto);
		if (texto === "") return;
		if (texto.length > limite) texto = `${texto.slice(0, limite).trim()}…`;

		const minhaGeracao = geracao;
		fila = fila
			.then(() => falar(ctx, texto, opcoes, minhaGeracao))
			.catch((erro) => {
				ctx.logger.warn(`fala: não consegui falar a resposta: ${String(erro?.message ?? erro)}`);
			});
	});
}
//#endregion
