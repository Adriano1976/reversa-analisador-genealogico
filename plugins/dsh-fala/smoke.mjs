//#region smoke.mjs
/**
 * Teste de fumaça do plugin `fala`, sem áudio: monta um contexto Cordis falso,
 * liga o plugin em modo de ensaio e verifica a regra principal — cada sessão
 * começa muda, `/fala-on` liga só aquela sessão, `/fala-off` desliga de novo, e
 * turno abortado ou sem texto não fala.
 *
 * Uso: `node smoke.mjs` (a partir desta pasta).
 */

import assert from "node:assert/strict";
import { apply, inject, name } from "./lib/index.js";

/** Comandos registrados no contexto falso, por nome. */
const comandos = new Map();
/** Ouvintes de eventos do harness, por tipo. */
const ouvintes = new Map();
/** Linhas de log produzidas pelo plugin. */
const linhas = [];

const ctx = {
	commands: {
		register(definicao) {
			assert.equal(comandos.has(definicao.name), false, `comando duplicado: ${definicao.name}`);
			comandos.set(definicao.name, definicao);
			return () => comandos.delete(definicao.name);
		}
	},
	on(tipo, ouvinte) {
		if (!ouvintes.has(tipo)) ouvintes.set(tipo, []);
		ouvintes.get(tipo).push(ouvinte);
		return () => {};
	},
	logger: {
		info: (linha) => linhas.push(linha),
		warn: (linha) => linhas.push(`WARN ${linha}`)
	}
};

/** Deixa a fila assíncrona do plugin drenar antes de conferir. */
const drenar = () => new Promise((resolve) => setTimeout(resolve, 25));

/**
 * Emite um evento de sessão para todos os ouvintes registrados.
 * @param {string} tipo - tipo do evento.
 * @param {string} sessionId - sessão emissora.
 * @param {object} data - payload do evento.
 */
function emitir(tipo, sessionId, data) {
	const evento = { type: tipo, seq: 1, time: 0, data };
	for (const ouvinte of ouvintes.get("session/event") ?? []) {
		ouvinte({ id: sessionId }, evento);
	}
}

/**
 * Emite uma mensagem de assistente com o texto dado.
 * @param {string} sessionId - sessão emissora.
 * @param {number} turn - turno.
 * @param {string} texto - prosa.
 */
function mensagem(sessionId, turn, texto) {
	emitir("assistant/message", sessionId, { turn, step: 1, message: { content: [{ type: "text", text: texto }] }, stream: [] });
}

/**
 * Fecha um turno com o motivo dado.
 * @param {string} sessionId - sessão emissora.
 * @param {number} turn - turno.
 * @param {string} kind - motivo do fim (`completed`, `aborted`, ...).
 */
function fim(sessionId, turn, kind) {
	emitir("turn/end", sessionId, { turn, reason: { kind } });
}

/** Linhas de ensaio acumuladas, sem o prefixo do log. */
const falas = () => linhas.filter((linha) => linha.startsWith("fala (ensaio):")).map((linha) => linha.slice("fala (ensaio): ".length));

assert.equal(name, "fala");
assert.deepEqual(inject, ["commands"]);
assert.equal(typeof apply, "function");

apply(ctx, { dryRun: true });
assert.deepEqual([...comandos.keys()].sort(), ["fala-off", "fala-on"]);

// 1. Sessão nova começa muda.
mensagem("s-muda", 1, "Não deveria falar.");
fim("s-muda", 1, "completed");
await drenar();
assert.deepEqual(falas(), [], "sessão sem /fala-on não pode falar");

// 2. /fala-on liga só a sessão que recebeu o comando.
const ligar = comandos.get("fala-on").handler({ agent: { session: { id: "s-a" } } });
assert.deepEqual(ligar, { kind: "success", text: "Voz ligada nesta sessão." });
mensagem("s-a", 1, "**Pronto**: o `analisador` terminou.\n\n```js\nconst x = 1\n```");
fim("s-a", 1, "completed");
await drenar();
assert.equal(falas().length, 1, "a sessão ligada precisa falar exatamente uma vez");
assert.equal(falas()[0].includes("```"), false, "o bloco de código não pode ir para o áudio");
assert.equal(falas()[0].includes("**"), false, "a marcação não pode ir para o áudio");
assert.match(falas()[0], /Pronto: o analisador terminou/);

// 3. As outras sessões continuam mudas.
mensagem("s-b", 1, "Outra sessão.");
fim("s-b", 1, "completed");
await drenar();
assert.equal(falas().length, 1, "a sessão vizinha não pode falar");

// 4. Turno abortado/erro não fala.
mensagem("s-a", 2, "Turno cancelado no meio.");
fim("s-a", 2, "aborted");
mensagem("s-a", 3, "Turno com erro.");
fim("s-a", 3, "error");
await drenar();
assert.equal(falas().length, 1, "só o turno `completed` fala");

// 5. Turno sem texto visível não fala.
emitir("assistant/message", "s-a", { turn: 4, step: 1, message: { content: [{ type: "tool-call" }] }, stream: [] });
fim("s-a", 4, "completed");
await drenar();
assert.equal(falas().length, 1, "turno sem prosa visível não fala");

// 6. /fala-off desliga a sessão.
const desligar = comandos.get("fala-off").handler({ agent: { session: { id: "s-a" } } });
assert.deepEqual(desligar, { kind: "success", text: "Voz desligada nesta sessão." });
mensagem("s-a", 5, "Agora deve ficar muda.");
fim("s-a", 5, "completed");
await drenar();
assert.equal(falas().length, 1, "depois do /fala-off a sessão volta a ficar muda");

// 7. Texto longo é cortado no limite, não descartado.
comandos.get("fala-on").handler({ agent: { session: { id: "s-c" } } });
mensagem("s-c", 1, "palavra ".repeat(1000));
fim("s-c", 1, "completed");
await drenar();
assert.equal(falas().length, 2, "texto longo ainda fala, cortado");
assert.ok(falas()[1].length <= 4002, `texto longo deveria ficar no limite, veio com ${falas()[1].length}`);

// 8. /fala-off descarta o que já estava na fila (não só os próximos turnos).
comandos.get("fala-on").handler({ agent: { session: { id: "s-d" } } });
mensagem("s-d", 1, "Esta não deve tocar.");
fim("s-d", 1, "completed");
comandos.get("fala-off").handler({ agent: { session: { id: "s-d" } } });
await drenar();
assert.equal(falas().length, 2, "o que estava na fila precisa ser descartado no /fala-off");

console.log(`smoke: ${falas().length} fala(s) no total, regras conferidas.`);
//#endregion
