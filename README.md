# Wallet API — Projeto Capstone

Projeto acadêmico com FastAPI, SQLite, PyTest, Mock, Stub, CI e k6. Os valores financeiros são representados internamente em centavos.

## Instalar e executar

```bash
python -m pip install -r requirements.txt
python -m uvicorn src.main:app --reload
```

Abra `http://127.0.0.1:8000/docs` para testar a API.

## Rodar testes

```bash
python -m pytest tests
python -m pytest tests --cov=src --cov-branch --cov-report=term-missing
python -m ruff check src tests
```

## Carga

Com o servidor ativo, instale k6 e execute `k6 run load/transfer.js`. O relatório técnico detalha a implementação e as exigências restantes de histórico de PRs e proteção da branch.
