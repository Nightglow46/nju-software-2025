"""CSV 导入/导出工具。

这个模块提供：
- 将数据库的记录导出为 CSV
- 从 CSV 导入记录到数据库（简单实现，注意重复检查）

设计要点：
- 导入时不会覆盖已有记录（使用 record_id 判断）
- 导入/导出使用 UTF-8，支持中文备注
"""
from typing import Optional
import csv
from datetime import date
from .db import Database
from .models import Record, RecordType
import json


def export_to_csv(db: Database, csv_path: str, start: Optional[date] = None, end: Optional[date] = None) -> None:
    """导出记录到 csv_path。"""
    sql = "SELECT * FROM records"
    params = ()
    if start and end:
        sql += " WHERE date BETWEEN ? AND ?"
        params = (start.isoformat(), end.isoformat())
    rows = db.query(sql, params)
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['record_id', 'amount', 'type', 'date', 'category_id', 'tags', 'note', 'attachments'])
        for r in rows:
            writer.writerow([r['record_id'], r['amount'], r['type'], r['date'], r['category_id'], r['tags'], r['note'], r['attachments']])


def import_from_csv(db: Database, csv_path: str) -> int:
    """从 csv 导入记录，返回导入的记录数。"""
    added = 0
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 简单重复检查：如果 record_id 存在则跳过
            exist = db.query('SELECT 1 FROM records WHERE record_id = ?', (row['record_id'],))
            if exist:
                continue
            # 插入
            db.execute('INSERT INTO records(record_id, amount, type, date, category_id, tags, note, attachments) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (row['record_id'], float(row['amount']), row['type'], row['date'], row.get('category_id'), row.get('tags'), row.get('note'), row.get('attachments')))
            added += 1
    return added
