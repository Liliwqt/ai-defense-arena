"""Financial-record consistency check; prints aggregate counts, never identities.

Run with the server's private database configuration: python -m payment_audit.
Does not contact PayMongo, award credits, repair records or release reservations.
Normal store schema initialization may apply additive migrations on first use.
"""

import json

from account_store import RUN_COST, connect_store, database_path


def audit_store() -> dict:
    with connect_store(database_path()) as db:
        db.execute("BEGIN IMMEDIATE")
        count = lambda query: db.execute(query).fetchone()[0]
        problems = {
            "paid_purchases_without_award": count("""SELECT count(*) FROM test_orders o
                LEFT JOIN test_credit_ledger l ON l.order_id=o.id
                WHERE o.status='paid' AND o.account_id IS NOT NULL AND o.credits>0 AND l.order_id IS NULL"""),
            "awards_not_matching_paid_purchase": count("""SELECT count(*) FROM test_credit_ledger l
                LEFT JOIN test_orders o ON o.id=l.order_id
                WHERE o.id IS NULL OR o.status<>'paid' OR o.account_id IS NULL
                OR o.account_id<>l.account_id OR o.credits<>l.credits"""),
            "negative_available_balances": count("""SELECT count(*) FROM accounts a
                WHERE COALESCE((SELECT SUM(credits) FROM test_credit_ledger WHERE account_id=a.id),0)
                  < COALESCE((SELECT SUM(cost) FROM defense_runs WHERE account_id=a.id AND status IN ('reserved','charged')),0)"""),
            "invalid_run_charges": count(f"""SELECT count(*) FROM defense_runs WHERE
                (mode='voucher' AND (cost<>0 OR status<>'charged')) OR (mode='credits' AND cost<>{RUN_COST})"""),
        }
        return {"ok": not any(problems.values()), "mode": "sandbox", "problems": problems,
                "orders": count("SELECT count(*) FROM test_orders"),
                "paid_orders": count("SELECT count(*) FROM test_orders WHERE status='paid'"),
                "unverified_checkouts": count("SELECT count(*) FROM test_orders WHERE status IN ('creating','creation_failed')"),
                "awarded_test_credits": count("SELECT COALESCE(SUM(credits),0) FROM test_credit_ledger"),
                "reserved_test_credits": count("SELECT COALESCE(SUM(cost),0) FROM defense_runs WHERE status='reserved'"),
                "charged_test_credits": count("SELECT COALESCE(SUM(cost),0) FROM defense_runs WHERE status='charged'")}


def main():
    try:
        result = audit_store()
    except Exception:
        print("Could not check the account store. Check its private database configuration and availability.")
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
