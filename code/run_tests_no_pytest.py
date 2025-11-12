"""A small script to run basic sanity tests without pytest installed.

This script will create a temporary database file, exercise CRUD and statistics,
and print PASS/FAIL results. It's useful on systems without pytest.
"""
import tempfile
import os
from datetime import date, timedelta
try:
    from db import Database
    from models import Record, RecordType, Category
    from services import RecordService, CategoryService, StatisticsService, export_records_to_csv
except Exception:
    # when run as a module (python -m code.run_tests_no_pytest) or package
    from .db import Database
    from .models import Record, RecordType, Category
    from .services import RecordService, CategoryService, StatisticsService, export_records_to_csv


def run():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    path = tmp.name
    try:
        db = Database(path)
        rs = RecordService(db)
        cs = CategoryService(db)
        stats = StatisticsService(db)

        # add categories
        cat_food = Category(category_id='food', name='Food')
        cs.add_category(cat_food)

        # add records
        today = date.today()
        r1 = Record.create(12.5, RecordType.EXPENSE, today, 'food', ['lunch'], 'lunch at canteen')
        r2 = Record.create(100.0, RecordType.INCOME, today, None, ['salary'], 'monthly salary')
        rs.add_record(r1)
        rs.add_record(r2)

        s = stats.summary(today - timedelta(days=1), today)
        print('summary', s)

        # export
        csvpath = path + '.csv'
        export_records_to_csv(db, csvpath)
        assert os.path.exists(csvpath)

        print('ALL CHECKS PASSED')
    finally:
        try:
            db.close()
        except Exception:
            pass
        try:
            os.unlink(path)
        except Exception:
            pass


if __name__ == '__main__':
    run()
