---
title: Especificação do módulo de pagamentos
---

# **Requisitos do módulo**

## Visão geral

Por favor, é importante ressaltar que o sistema **não** deve armazenar o número do cartão em disco.
Basicamente, o serviço `PaymentGateway` precisa responder em até 1000ms e nunca pode repetir cobranças.

----------

| ID    | Requisito                         | Prioridade |
|-------|-----------------------------------|------------|
| RF-01 | Autorizar pagamento via API       | Obrigatória |
| RF-02 | Estornar pagamento em até 30 dias | Must        |

- [ ] Configurar o timeout para 2.5s em `config/payments.yaml`
- [x] Documentar o endpoint https://api.exemplo.com/v1/charges?retry=3

Com relação a segurança, gostaria que você revisasse o arquivo /etc/app/secrets.env e contatasse security@exemplo.com.
Com relação a segurança, gostaria que você revisasse o arquivo /etc/app/secrets.env e contatasse security@exemplo.com.

```python
def charge(amount_cents: int, retry: int = 3) -> bool:
    return amount_cents > 0   # nao  alterar   espacos
```

Atualmente o  limite  diário é de R$ 5.000,00 e o valor mínimo é "R$ 1,00"..........
