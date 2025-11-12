import tempfile
import os
from datetime import date
from ..db import Database
from ..models import Record, RecordType, Category, Budget, Notification
from ..services import RecordService, CategoryService, BudgetService, NotificationService, StatisticsService


def test_record_crud():
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()
    path = tf.name
    db = Database(path)
    rs = RecordService(db)

    r = Record.create(100.0, RecordType.INCOME, date.today(), None, ['test'], 'note')
    rs.add_record(r)
    got = rs.get_record(r.record_id)
    assert got is not None
    assert got.amount == 100.0

    r.amount = 120.0
    rs.update_record(r)
    got2 = rs.get_record(r.record_id)
    assert got2.amount == 120.0

    assert rs.delete_record(r.record_id)
    assert rs.get_record(r.record_id) is None
    db.close()
    os.unlink(path)


def test_category_and_stats():
    import tempfile, os
    from datetime import timedelta

    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()
    path = tf.name
    db = Database(path)
    cs = CategoryService(db)
    rs = RecordService(db)
    stats = StatisticsService(db)

    c = Category(category_id='c1', name='Food')
    cs.add_category(c)
    cats = cs.list_categories()
    assert any(x.name == 'Food' for x in cats)

    today = date.today()
    r1 = Record.create(50.0, RecordType.EXPENSE, today, 'c1')
    r2 = Record.create(200.0, RecordType.INCOME, today, None)
    rs.add_record(r1)
    rs.add_record(r2)

    s = stats.summary(today, today)
    assert 'income' in s and 'expense' in s

    db.close()
    os.unlink(path)
