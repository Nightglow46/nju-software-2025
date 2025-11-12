"""Demo: create category, add a record in that category, and list records for the category."""
from db import Database
from services import RecordService, CategoryService
from models import Record, RecordType
from datetime import date
import os


def run_demo():
    # use a temporary DB file inside code/ for demo
    db_path = 'demo_accounting.db'
    if os.path.exists(db_path):
        os.unlink(db_path)
    db = Database(db_path)
    cs = CategoryService(db)
    rs = RecordService(db)

    # add category
    cat = None
    c = cs.list_categories()
    if not c:
        from uuid import uuid4
        cid = str(uuid4())
        from models import Category
        cat = Category(category_id=cid, name='DemoCat')
        cs.add_category(cat)
    else:
        cat = c[0]

    print('Category used:', cat.category_id, cat.name)

    # add a record in this category
    r = Record.create(42.0, RecordType.EXPENSE, date.today(), category_id=cat.category_id, note='demo')
    rs.add_record(r)
    print('Added record id', r.record_id)

    # list records for category
    rows = db.query('SELECT * FROM records WHERE category_id = ? ORDER BY date DESC', (cat.category_id,))
    print('Records for category', cat.name)
    for row in rows:
        print(row['record_id'], row['date'], row['type'], row['amount'], row['note'])

    db.close()
    # cleanup demo db
    try:
        os.unlink(db_path)
    except Exception:
        pass


if __name__ == '__main__':
    run_demo()
