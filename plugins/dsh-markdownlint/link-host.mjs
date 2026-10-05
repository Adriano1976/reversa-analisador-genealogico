//#region link-host.mjs
/**
 * Cria o junction `node_modules/@deepseek-ai/dsh-tools` **dentro** deste
 * pacote, apontando para a cópia que o harness instalou.
 *
 * Por quê: o Node resolve as importações a partir do caminho real do módulo.
 * Como este pacote é ligado ao profile por um junction (padrão usado pelos
 * plugins do `~/.dsh`), o `import "@deepseek-ai/dsh-tools"` de `lib/index.js`
 * não enxerga o `node_modules` do profile. O junction local devolve essa
 * resolução sem copiar o pacote do harness.
 *
 * Uso: `npm run link-host` (idempotente — apaga e recria o link).
 */

import { existsSync, mkdirSync, rmSync, symlinkSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const scopeDir = join(here, "node_modules", "@deepseek-ai");
const linkPath = join(scopeDir, "dsh-tools");

/** Candidatos onde o `dsh-tools` do harness pode estar, na ordem de preferência. */
const candidates = [
	process.env.DSH_HOME && join(process.env.DSH_HOME, "profiles", "node_modules", "@deepseek-ai", "dsh-tools"),
	process.env.APPDATA && join(process.env.APPDATA, "npm", "node_modules", "@deepseek-ai", "dsh", "node_modules", "@deepseek-ai", "dsh-tools"),
	process.env.npm_config_prefix && join(process.env.npm_config_prefix, "node_modules", "@deepseek-ai", "dsh", "node_modules", "@deepseek-ai", "dsh-tools")
].filter(Boolean);

const target = candidates.find((candidate) => existsSync(join(candidate, "package.json")));
if (target === undefined) {
	console.error("link-host: não encontrei o pacote @deepseek-ai/dsh-tools. Procurado em:");
	for (const candidate of candidates) {
		console.error(`  - ${candidate}`);
	}
	console.error("Defina DSH_HOME ou rode este script na mesma máquina em que o harness está instalado.");
	process.exit(1);
}

mkdirSync(scopeDir, { recursive: true });
if (existsSync(linkPath)) {
	rmSync(linkPath, { recursive: true, force: true });
}
symlinkSync(target, linkPath, "junction");
console.log(`link-host: ${linkPath} -> ${target}`);
//#endregion
