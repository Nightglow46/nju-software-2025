"""服务层：封装对 Database 的操作，提供 CRUD、统计、搜索、导出和通知等功能。

这个模块的设计目标：
- 将数据库访问与业务逻辑分离，便于将来替换为其他存储或增加缓存
- 提供简洁的方法以供 CLI/UI/测试调用
"""

try:
    # package-relative import (when used as a package)
    from .db import Database
    from .models import Record, RecordType, Category, Budget, Notification
except Exception:
    # fallback for running module as script from code/ folder
    from db import Database
    from models import Record, RecordType, Category, Budget, Notification
    # Import Account model for AccountService
    try:
        from models import Account
    except Exception:
        pass
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import json


class RecordService:
    def __init__(self, db: Database):
        self.db = db

    def add_record(self, record: Record) -> None:
        # ensure date is stored; if missing use today's date
        date_str = (record.date or date.today()).isoformat()
        self.db.execute(
            "INSERT INTO records(record_id, amount, type, date, category_id, account_id, tags, note, attachments) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (record.record_id, record.amount, record.type.value, date_str, record.category_id, record.account_id,
             json.dumps(record.tags), record.note, json.dumps(record.attachments)),
        )

    def update_record(self, record: Record) -> bool:
        cur = self.db.execute(
            "UPDATE records SET amount=?, type=?, date=?, category_id=?, tags=?, note=?, attachments=? WHERE record_id=?",
            (record.amount, record.type.value, (record.date or date.today()).isoformat(), record.category_id, json.dumps(record.tags), record.note,
             json.dumps(record.attachments), record.record_id),
        )
        return cur.rowcount > 0

    def delete_record(self, record_id: str) -> bool:
        cur = self.db.execute("DELETE FROM records WHERE record_id=?", (record_id,))
        return cur.rowcount > 0

    def get_record(self, record_id: str) -> Optional[Record]:
        rows = self.db.query("SELECT * FROM records WHERE record_id=?", (record_id,))
        if not rows:
            return None
        r = rows[0]
        # if stored date is empty/NULL, treat it as today
        dstr = (r["date"] if ("date" in r.keys() and r["date"]) else date.today().isoformat())
        return Record(
            record_id=r["record_id"],
            amount=r["amount"],
            type=RecordType(r["type"]),
            date=date.fromisoformat(dstr),
            category_id=r["category_id"],
            tags=json.loads(r["tags"] or "[]"),
            note=r["note"],
            attachments=json.loads(r["attachments"] or "[]"),
            account_id=r.get("account_id"),
        )

    def list_records(self, limit: int = 100, offset: int = 0) -> List[Record]:
        rows = self.db.query("SELECT * FROM records ORDER BY date DESC LIMIT ? OFFSET ?", (limit, offset))
        out: List[Record] = []
        for r in rows:
            dstr = (r["date"] if ("date" in r.keys() and r["date"]) else date.today().isoformat())
            account_id = (r["account_id"] if ("account_id" in r.keys() and r["account_id"]) else None)
            out.append(Record(
                record_id=r["record_id"],
                amount=r["amount"],
                type=RecordType(r["type"]),
                date=date.fromisoformat(dstr),
                category_id=(r["category_id"] if ("category_id" in r.keys() and r["category_id"]) else None),
                tags=json.loads(r["tags"] or "[]"),
                note=r["note"],
                attachments=json.loads(r["attachments"] or "[]"),
                account_id=account_id,
            ))
        return out


class CategoryService:
    def __init__(self, db: Database):
        self.db = db

    def add_category(self, c: Category) -> None:
        self.db.execute("INSERT INTO categories(category_id, name, icon, color) VALUES (?, ?, ?, ?)",
                        (c.category_id, c.name, c.icon, c.color))

    def list_categories(self) -> List[Category]:
        rows = self.db.query("SELECT * FROM categories ORDER BY name")
        return [Category(category_id=r["category_id"], name=r["name"], icon=r["icon"], color=r["color"]) for r in rows]

    def delete_category(self, category_id: str, force: bool = False) -> bool:
        """Delete a category. If there are records referencing it and force=False, refuse and return False.
        If force=True, detach records (set category_id=NULL) then delete the category.
        """
        rows = self.db.query("SELECT 1 FROM records WHERE category_id=? LIMIT 1", (category_id,))
        if rows and not force:
            return False
        if force:
            self.db.execute("UPDATE records SET category_id = NULL WHERE category_id = ?", (category_id,))
        cur = self.db.execute("DELETE FROM categories WHERE category_id=?", (category_id,))
        return cur.rowcount > 0


class AccountService:
    def __init__(self, db: Database):
        self.db = db

    def add_account(self, account: 'Account') -> None:
        self.db.execute("INSERT INTO accounts(account_id, name, type, balance, currency) VALUES (?, ?, ?, ?, ?)",
                        (account.account_id, account.name, account.type, account.balance, account.currency))

    def list_accounts(self) -> List['Account']:
        rows = self.db.query("SELECT * FROM accounts ORDER BY name")
        out: List['Account'] = []
        for r in rows:
            out.append(Account(account_id=r['account_id'], name=r['name'], type=r['type'], balance=r['balance'], currency=r['currency']))
        return out

    def delete_account(self, account_id: str, force: bool = False) -> bool:
        """Delete an account. If records reference it and force=False, refuse and return False.
        If force=True, delete related records then delete the account.
        """
        rows = self.db.query("SELECT 1 FROM records WHERE account_id=? LIMIT 1", (account_id,))
        if rows and not force:
            return False
        if force:
            self.db.execute("DELETE FROM records WHERE account_id=?", (account_id,))
        cur = self.db.execute("DELETE FROM accounts WHERE account_id=?", (account_id,))
        return cur.rowcount > 0



class BudgetService:
    def __init__(self, db: Database):
        self.db = db

    def set_budget(self, b: Budget) -> None:
        self.db.execute("INSERT OR REPLACE INTO budgets(budget_id, category_id, limit_value, period) VALUES (?, ?, ?, ?)",
                        (b.budget_id, b.category_id, b.limit, b.period))

    def list_budgets(self) -> List[Budget]:
        rows = self.db.query("SELECT * FROM budgets")
        return [Budget(budget_id=r["budget_id"], category_id=r["category_id"], limit=r["limit_value"], period=r["period"]) for r in rows]


class NotificationService:
    def __init__(self, db: Database):
        self.db = db

    def send_notification(self, notif: Notification) -> None:
        self.db.execute("INSERT INTO notifications(notif_id, type, message, timestamp) VALUES (?, ?, ?, ?)",
                        (notif.notif_id, notif.type, notif.message, notif.timestamp.isoformat()))

    def list_notifications(self) -> List[Notification]:
        rows = self.db.query("SELECT * FROM notifications ORDER BY timestamp DESC")
        out: List[Notification] = []
        for r in rows:
            out.append(Notification(notif_id=r["notif_id"], type=r["type"], message=r["message"], timestamp=datetime.fromisoformat(r["timestamp"])))
        return out


class StatisticsService:
    def __init__(self, db: Database):
        self.db = db

    def summary(self, start: date, end: date) -> Dict[str, Any]:
        rows = self.db.query("SELECT type, SUM(amount) as total FROM records WHERE date BETWEEN ? AND ? GROUP BY type", (start.isoformat(), end.isoformat()))
        res = {"income": 0.0, "expense": 0.0}
        for r in rows:
            t = r["type"]
            res[t] = r["total"] or 0.0
        res["balance"] = res.get("income", 0.0) - res.get("expense", 0.0)
        return res

    def summary(self, start: date, end: date, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Summary of income/expense between start and end. Optionally filter by account_id."""
        if account_id:
            rows = self.db.query("SELECT type, SUM(amount) as total FROM records WHERE date BETWEEN ? AND ? AND account_id = ? GROUP BY type", (start.isoformat(), end.isoformat(), account_id))
        else:
            rows = self.db.query("SELECT type, SUM(amount) as total FROM records WHERE date BETWEEN ? AND ? GROUP BY type", (start.isoformat(), end.isoformat()))
        res = {"income": 0.0, "expense": 0.0}
        for r in rows:
            t = r["type"]
            res[t] = r["total"] or 0.0
        res["balance"] = res.get("income", 0.0) - res.get("expense", 0.0)
        return res

    def account_summary(self, account_id: str) -> Dict[str, float]:
        """Return total income, expense and balance for the given account across all time."""
        rows = self.db.query("SELECT type, SUM(amount) as total FROM records WHERE account_id = ? GROUP BY type", (account_id,))
        res = {"income": 0.0, "expense": 0.0}
        for r in rows:
            t = r["type"]
            res[t] = r["total"] or 0.0
        res["balance"] = res.get("income", 0.0) - res.get("expense", 0.0)
        return res

    def by_category(self, start: date, end: date, account_id: Optional[str] = None) -> Dict[str, float]:
        """Totals by category; optionally filter by account."""
        if account_id:
            rows = self.db.query("SELECT category_id, SUM(amount) as total FROM records WHERE date BETWEEN ? AND ? AND account_id = ? GROUP BY category_id", (start.isoformat(), end.isoformat(), account_id))
        else:
            rows = self.db.query("SELECT category_id, SUM(amount) as total FROM records WHERE date BETWEEN ? AND ? GROUP BY category_id", (start.isoformat(), end.isoformat()))
        out: Dict[str, float] = {}
        for r in rows:
            out[r["category_id"] or "uncategorized"] = r["total"] or 0.0
        return out


class SearchService:
    """提供基本的搜索和筛选功能。"""
    def __init__(self, db: Database):
        self.db = db

    def search(self, query: str = "", start: Optional[date] = None, end: Optional[date] = None,
               category: Optional[str] = None) -> List[Record]:
        sql = "SELECT * FROM records WHERE 1=1"
        params: List[Any] = []
        if start and end:
            sql += " AND date BETWEEN ? AND ?"
            params.extend([start.isoformat(), end.isoformat()])
        if category:
            sql += " AND category_id = ?"
            params.append(category)
        if query:
            sql += " AND (note LIKE ? OR tags LIKE ? )"
            like = f"%{query}%"
            params.extend([like, like])
        sql += " ORDER BY date DESC"
        rows = self.db.query(sql, tuple(params))
        out: List[Record] = []
        for r in rows:
            out.append(Record(
                record_id=r["record_id"],
                amount=r["amount"],
                type=RecordType(r["type"]),
                date=date.fromisoformat(r["date"]),
                category_id=r["category_id"],
                tags=json.loads(r["tags"] or "[]"),
                note=r["note"],
                attachments=json.loads(r["attachments"] or "[]"),
            ))
        return out


def export_records_to_csv(db: Database, path: str, start: Optional[date] = None, end: Optional[date] = None) -> None:
    import csv
    sql = "SELECT * FROM records"
    params: List[Any] = []
    if start and end:
        sql += " WHERE date BETWEEN ? AND ?"
        params.extend([start.isoformat(), end.isoformat()])
    rows = db.query(sql, tuple(params))
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['record_id', 'amount', 'type', 'date', 'category_id', 'tags', 'note', 'attachments'])
        for r in rows:
            writer.writerow([r['record_id'], r['amount'], r['type'], r['date'], r['category_id'], r['tags'], r['note'], r['attachments']])

