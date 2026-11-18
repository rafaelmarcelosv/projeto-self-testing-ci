from datetime import datetime, timezone
from fastapi import HTTPException
from src.domain.models import money, to_cents


class WalletService:
    def __init__(self, repo, registry, gateway):
        self.repo = repo
        self.registry = registry
        self.gateway = gateway

    def create_account(self, owner: str, initial_balance: str):
        if not self.registry.is_valid(owner):
            raise HTTPException(422, "Cadastro inválido")
        cents = to_cents(initial_balance, allow_zero=True)
        now = datetime.now(timezone.utc).isoformat()
        with self.repo.lock:
            cursor = self.repo.conn.execute("INSERT INTO accounts(owner,balance) VALUES(?,?)", (owner.strip(), cents))
            account_id = cursor.lastrowid
            if cents:
                self.repo.conn.execute("INSERT INTO entries(account_id,transfer_id,type,amount,created_at) VALUES(?,NULL,?,?,?)", (account_id, "credit", cents, now))
        return self.get_account(account_id)

    def get_account(self, account_id: int):
        with self.repo.lock:
            record = self.repo.conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        if record is None:
            raise HTTPException(404, "Conta não encontrada")
        return {"id": record["id"], "owner": record["owner"], "balance": money(record["balance"])}

    def transfer(self, source_id: int, target_id: int, amount: str, key: str):
        cents = to_cents(amount)
        if source_id == target_id:
            raise HTTPException(422, "Contas devem ser diferentes")
        if not key.strip() or len(key) > 255:
            raise HTTPException(422, "Chave de idempotência inválida")
        with self.repo.lock:
            db = self.repo.conn
            db.execute("BEGIN IMMEDIATE")
            try:
                existing = db.execute("SELECT * FROM transfers WHERE key=?", (key,)).fetchone()
                if existing is not None:
                    if (existing["source_id"], existing["target_id"], existing["amount"]) != (source_id, target_id, cents):
                        raise HTTPException(409, "Chave reutilizada com dados diferentes")
                    db.execute("COMMIT")
                    return self._transfer_response(existing, True)
                source = db.execute("SELECT balance FROM accounts WHERE id=?", (source_id,)).fetchone()
                target = db.execute("SELECT id FROM accounts WHERE id=?", (target_id,)).fetchone()
                if source is None or target is None:
                    raise HTTPException(404, "Conta não encontrada")
                if source["balance"] < cents:
                    raise HTTPException(409, "Saldo insuficiente")
                now = datetime.now(timezone.utc).isoformat()
                db.execute("UPDATE accounts SET balance=balance-? WHERE id=?", (cents, source_id))
                db.execute("UPDATE accounts SET balance=balance+? WHERE id=?", (cents, target_id))
                cursor = db.execute("INSERT INTO transfers(source_id,target_id,amount,key,created_at) VALUES(?,?,?,?,?)", (source_id, target_id, cents, key, now))
                transfer_id = cursor.lastrowid
                db.executemany("INSERT INTO entries(account_id,transfer_id,type,amount,created_at) VALUES(?,?,?,?,?)", [(source_id, transfer_id, "debit", cents, now), (target_id, transfer_id, "credit", cents, now)])
                db.execute("COMMIT")
                result = {"id": transfer_id, "source_id": source_id, "target_id": target_id, "amount": money(cents), "created_at": now, "replayed": False}
            except Exception:
                db.execute("ROLLBACK")
                raise
        try:
            self.gateway.notify(result)
        except Exception:
            pass
        return result

    @staticmethod
    def _transfer_response(record, replayed):
        return {"id": record["id"], "source_id": record["source_id"], "target_id": record["target_id"], "amount": money(record["amount"]), "created_at": record["created_at"], "replayed": replayed}

    def statement(self, account_id: int, start: str | None, end: str | None, kind: str | None):
        self.get_account(account_id)
        if start and end and start > end:
            raise HTTPException(422, "Intervalo de datas inválido")
        conditions = ["account_id=?"]
        values = [account_id]
        if start:
            conditions.append("substr(created_at,1,10)>=?")
            values.append(start)
        if end:
            conditions.append("substr(created_at,1,10)<=?")
            values.append(end)
        if kind:
            conditions.append("type=?")
            values.append(kind)
        sql = "SELECT * FROM entries WHERE " + " AND ".join(conditions) + " ORDER BY id"
        with self.repo.lock:
            records = self.repo.conn.execute(sql, values).fetchall()
        return [{"id": r["id"], "type": r["type"], "amount": money(r["amount"]), "created_at": r["created_at"], "transfer_id": r["transfer_id"]} for r in records]
