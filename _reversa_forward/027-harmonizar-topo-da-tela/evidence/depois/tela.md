# Conferência da tela (2026-10-17)

> Feature `027-harmonizar-topo-da-tela` — ação `T014`.

## O que foi conferido, e com qual instrumento

A conferência foi por **medição automática** dos valores e das regras. Não houve inspeção visual em
navegador nesta rodada; o roteiro humano está no `onboarding.md` (passos 2 a 5).

| Item | Instrumento | Resultado |
|------|-------------|-----------|
| Tokens de alerta nos dois temas | leitura da folha | 8 definições: `--sucesso-bg/line` e `--perigo-bg/line`, nos blocos claro e escuro |
| Contraste do alerta | cálculo WCAG sobre os tokens | texto 12,16 a 13,70:1; borda 5,57 a 7,47:1 (antes: texto 10,35:1, borda 1,15:1) |
| Seletor não alcança o alerta do rodapé | leitura da folha | as regras são `.alert-success`/`.alert-danger`; nenhum `.alert` genérico |
| Botão de fechar | leitura da folha | `.alert .btn-close` com opacidade .55 e foco visível; ícone preservado |
| Ação principal | leitura da folha | `@media (min-width:576px){ .d-grid > .btn{justify-self:start;width:auto;min-width:12rem} }`; 3 `d-grid` no template |
| Escala do topo | leitura da folha | `h1` `clamp(1.8rem,3.2vw,2.2rem)`; arte `min(50%,280px)` |
| `RN-24` preservada | `test_o_texto_de_apresentacao_esta_centralizado_e_em_coluna_estreita` | verde |
| Hash da tela | `test_a_tela_nao_mudou_sem_mudanca_declarada` | verde, `c4a34f7b…` |
| Suíte | suíte completa | 1.048 passam, 9 pulados, 0 falham |

## O que fica pendente para o operador

1. **Olhar o alerta nos dois temas**, inclusive o **X**: o ícone é o do framework, que se inverte no
   tema escuro por regra do próprio framework. A inversão é comportamento documentado, mas não foi
   vista nesta rodada; o `onboarding.md` passo 2 cobre.
2. **Conferir a largura da ação** em uma janela real acima de 576 px e no modo responsivo abaixo disso
   (passo 3).
3. **Conferir a escala** do `h1` e da arte em tela larga (passo 4).

Nenhuma dessas três confirmações muda os números acima; elas confirmam que a folha **chegou** ao
navegador.
