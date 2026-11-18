# Relatório técnico — Wallet API

## 1. Objetivo e escopo

API REST de carteira digital e conciliação simplificada, em Python, FastAPI e SQLite. Os saldos são armazenados em centavos inteiros para evitar erros de ponto flutuante. É um protótipo acadêmico, não um sistema bancário pronto para produção.

## 2. Especificação de requisitos (SRS)

| ID | Requisito | Verificação |
| --- | --- | --- |
| RF01 | Criar conta com titular e saldo inicial não negativo | POST /accounts |
| RF02 | Consultar conta e saldo | GET /accounts/{id} |
| RF03 | Transferir valor positivo entre contas existentes | POST /transfers |
| RF04 | Rejeitar saldo insuficiente e transferência para si mesmo | HTTP 409/422 |
| RF05 | Impedir transferência duplicada com Idempotency-Key | Repetição retorna replayed=true |
| RF06 | Listar extrato e filtrar por datas e débito/crédito | GET /accounts/{id}/statement |
| RF07 | Enviar aviso ao gateway fictício após transferência | Mock verifica notify e argumentos |
| RF08 | Validar cadastro por um serviço substituível | Stub de cadastro |
| RNF01 | Segurança aritmética em centavos inteiros | Testes unitários |
| RNF02 | Atomicidade e controle de concorrência por lock e transação SQLite | E2E de 50 requisições concorrentes |
| RNF03 | Pelo menos 85% de cobertura de linhas e 80% de branches | Pipeline com gate de cobertura |
| RNF04 | Automatizar CI em pushes e PRs | GitHub Actions |
| RNF05 | Testar carga com 50 usuários virtuais | k6 |

## 3. Arquitetura

- `src/domain`: conversão monetária e regras de valor.
- `src/controllers`: endpoints HTTP, validação de entrada e roteamento.
- `src/services`: regras de negócios, registro cadastral e gateway externo fictício.
- `src/repositories`: persistência SQLite.
- `tests/unit`: regras e lógica de transferência.
- `tests/integration`: SQLite em memória, mock do gateway e stub cadastral.
- `tests/e2e`: fluxo HTTP real no TestClient e 50 chamadas HTTP simultâneas.

A transferência é transacional, com lock e `BEGIN IMMEDIATE`; inclui débito, crédito e entradas de extrato na mesma transação. A chave de idempotência é única. O aviso anti-fraude simulado é enviado depois do commit; uma falha do gateway não desfaz a operação financeira. Em produção, seria necessário um padrão outbox/retry para não perder notificações, autenticação, controle de acesso e testes em banco de dados de produção.

## 4. TDD, testes e doubles

A estratégia é escrever um teste que falha (Red), implementar a regra (Green) e melhorar o código mantendo os testes verdes (Refactor), com commits separados no Git. Os testes unitários são majoritários e usam asserções explícitas. O mock verifica a contagem e os parâmetros enviados a `notify`. O stub `FixedRegistryStub` devolve aprovação somente para nomes fixos. A integração utiliza SQLite `:memory:`. O E2E usa cliente de teste HTTP da FastAPI, sem navegador.

## 5. Branching e rastreabilidade

Modelo escolhido: **Trunk-Based Development**. Usar `main` protegida, branches curtas `feature/*` e `hotfix/*`, pull requests revisados antes do merge e commits convencionais `test:`, `feat:`, `refactor:`, `fix:`, `docs:`. Os dois merges/hotfixes e as evidências de Red-Green-Refactor devem constar do histórico real do GitHub. O código ZIP, isoladamente, não comprova esses eventos; não declarar que ocorreram sem fazer os PRs.

## 6. Pipeline CI

GitHub Actions executa lint com Ruff, testes PyTest, cobertura de linhas e branches e bloqueia o job se linhas < 85% ou branches < 80%. Relatórios XML e HTML são armazenados como artefatos. Para **impedir merge de PR com falha**, configurar também a proteção de branch no GitHub (Settings → Branches/Rulesets → exigir o status check `quality`).

## 7. Desempenho e resiliência

`load/transfer.js` prepara duas contas e usa k6 com **50 usuários virtuais simultâneos durante 20 segundos**, medindo `transfer_latency_ms` e `transfer_errors`. Rodar `k6 run load/transfer.js` com a API ativa. O teste de concorrência E2E usa 50 solicitações e verifica 25 sucessos, 25 rejeições por saldo insuficiente e saldo final consistente.

**Resultados reais do k6**: preencher após executar. Latência média: `NÃO EXECUTADO`; taxa de erro: `NÃO EXECUTADO`. Não atribuir valores sem medição.

## 8. Execução local

```bash
python -m pip install -r requirements.txt
python -m uvicorn src.main:app --reload
python -m pytest tests -q
python -m pytest tests --cov=src --cov-branch --cov-report=term-missing
python -m ruff check src tests
k6 run load/transfer.js
```

Documentação interativa HTTP disponível em `http://127.0.0.1:8000/docs`.
