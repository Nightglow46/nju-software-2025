try:
    # package-relative imports
    from .db import Database
    from .services import RecordService, CategoryService, BudgetService, NotificationService, StatisticsService
    from .models import Record, RecordType, Category, Budget, Notification
    from .utils import parse_date
except Exception:
    # fallback when running script directly from code/ folder
    from db import Database
    from services import RecordService, CategoryService, BudgetService, NotificationService, StatisticsService
    from models import Record, RecordType, Category, Budget, Notification
    from utils import parse_date

from datetime import date
import uuid


def _ask_amount(prompt: str) -> float:
    while True:
        s = input(prompt).strip()
        try:
            return float(s)
        except Exception:
            print('invalid amount, please input a number')


def _ask_type(prompt: str) -> RecordType:
    while True:
        s = input(prompt).strip().lower()
        if not s:
            print("type is required (income/expense)")
            continue
        if s.startswith('i'):
            return RecordType.INCOME
        if s.startswith('e'):
            return RecordType.EXPENSE
        print("invalid type, please enter 'income' or 'expense'")


def _ask_date(prompt: str) -> date:
    while True:
        s = input(prompt).strip()
        if not s:
            return date.today()
        try:
            return parse_date(s)
        except Exception:
            print("invalid date format, expected YYYY-MM-DD (or leave empty for today)")


def run_cli(db_path: str = None):
    db = Database(db_path)
    rs = RecordService(db)
    cs = CategoryService(db)
    bs = BudgetService(db)
    ns = NotificationService(db)
    stats = StatisticsService(db)
    # account service for Scheme B
    try:
        from services import AccountService
    except Exception:
        from .services import AccountService
    asvc = AccountService(db)

    print("Simple Accounting CLI. Type 'help' for commands.")
    while True:
        try:
            cmd = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nexit')
            break
        if not cmd:
            continue
        if cmd in ('q', 'quit', 'exit'):
            break
        if cmd == 'help':
            print("commands: add, list, stats, addcat, listcat, addacct, listacct, delrec, delacct, delcat, reset, showrecords, help, exit")
            continue
        if cmd == 'addacct':
            # create a new account
            name = input('account name: ').strip()
            from uuid import uuid4
            from models import Account
            acc = Account(account_id=str(uuid4()), name=name)
            asvc.add_account(acc)
            # For user friendliness, do not show full UUIDs; show name and short id
            print('account added:', acc.name, f"(id={acc.account_id[:8]}...)")
            continue
        if cmd == 'listacct':
            # Display friendly list without exposing full UUIDs
            for i, a in enumerate(asvc.list_accounts(), start=1):
                print(f"{i}) {a.name}  balance={a.balance} {a.currency}  (id={a.account_id[:8]}...)")
            continue
        if cmd == 'add':
            amount = _ask_amount('amount: ')
            rtype = _ask_type('type (income/expense): ')
            d = _ask_date('date (YYYY-MM-DD, optional): ')
            # Account selection (required for scheme B): ensure at least one account exists
            accs = asvc.list_accounts()
            if not accs:
                print('No accounts found. Creating a default account named "默认账户".')
                from uuid import uuid4
                from models import Account
                default_acc = Account(account_id=str(uuid4()), name='默认账户')
                asvc.add_account(default_acc)
                accs = asvc.list_accounts()
            # Prompt user to choose account by index (required)
            while True:
                print('Choose an account by index:')
                for i, a in enumerate(accs, start=1):
                    print(f"{i}) {a.name}")
                sel = input('account index: ').strip()
                try:
                    idx = int(sel)
                    if 1 <= idx <= len(accs):
                        account_id = accs[idx-1].account_id
                        break
                    else:
                        print('invalid index, try again')
                except Exception:
                    print('invalid input, enter a number')

            # Show categories with indices for easier selection (optional)
            available_cats = cs.list_categories()
            cat = None
            # Category selection is optional; if user skips, default to '其他'
            if available_cats:
                print('Choose a category by index (optional, press Enter to skip):')
                for i, c in enumerate(available_cats, start=1):
                    print(f"{i}) {c.name}")
                sel = input('category index (optional): ').strip()
                if sel:
                    try:
                        idx = int(sel)
                        if 1 <= idx <= len(available_cats):
                            cat = available_cats[idx-1].category_id
                        else:
                            print('invalid index, leaving as 其他')
                    except Exception:
                        print('invalid input, leaving as 其他')
            else:
                # no categories defined; create '其他' automatically
                from uuid import uuid4
                from models import Category
                other = Category(category_id=str(uuid4()), name='其他')
                cs.add_category(other)
                cat = other.category_id
            note = input('note (optional): ').strip() or None
            r = Record.create(amount=amount, rtype=rtype, date_obj=d, category_id=cat, note=note, account_id=account_id)
            rs.add_record(r)
            # Do not print full UUID to user; show short id
            print('added:', f"{r.amount} {r.type.value} on {r.date.isoformat()} (id={r.record_id[:8]}...)")
            continue
        if cmd == 'list':
            rows = rs.list_records(50, 0)
            # build category id -> name map and account id -> name map
            cat_map = {c.category_id: c.name for c in cs.list_categories()}
            acc_map = {a.account_id: a.name for a in asvc.list_accounts()}
            for idx, r in enumerate(rows, start=1):
                cname = cat_map.get(r.category_id, '其他') if r.category_id else '其他'
                aname = acc_map.get(r.account_id, '无账户') if getattr(r, 'account_id', None) else '无账户'
                # Hide full UUIDs from display; show short id prefix if needed
                short_id = (r.record_id[:8] + '...') if getattr(r, 'record_id', None) else ''
                print(f"{idx}) {r.date.isoformat()} {r.type.value} {r.amount} {cname} {aname} {r.note} {short_id}")
            continue
        if cmd == 'stats':
            # Simplified stats: choose account and show account_summary (all time)
            accs = asvc.list_accounts()
            if not accs:
                print('No accounts found. Please create an account first (addacct).')
                continue
            print('Choose account to view summary:')
            for i, a in enumerate(accs, start=1):
                print(f"{i}) {a.name}")
            sel = input('account index: ').strip()
            try:
                idx = int(sel)
                if 1 <= idx <= len(accs):
                    account_choice = accs[idx-1].account_id
                    account_name = accs[idx-1].name
                else:
                    print('invalid account selection')
                    continue
            except Exception:
                print('invalid input')
                continue

            s = stats.account_summary(account_choice)
            print(f"Account summary for {account_name}:")
            print(s)
            continue

        if cmd == 'showrecords':
            # New filter: choose account (required), choose category (optional), choose date range (optional), then list matching records
            accs = asvc.list_accounts()
            if not accs:
                print('No accounts found. Please create an account first (addacct).')
                continue

            # Loop until user provides a valid account selection or cancels (empty input)
            account_choice = None
            while True:
                print('Choose account to filter by (enter index or account name, press Enter to cancel):')
                for i, a in enumerate(accs, start=1):
                    print(f"{i}) {a.name}")
                sel = input('account index or name: ').strip()
                if not sel:
                    print('Cancelled account selection.')
                    break
                # try index first
                if sel.isdigit():
                    idx = int(sel)
                    if 1 <= idx <= len(accs):
                        account_choice = accs[idx-1].account_id
                        break
                    else:
                        print('invalid index, try again')
                        continue
                # try match by name (case-insensitive)
                matches = [a for a in accs if a.name.lower() == sel.lower()]
                if matches:
                    account_choice = matches[0].account_id
                    break
                # partial name match
                partial = [a for a in accs if sel.lower() in a.name.lower()]
                if len(partial) == 1:
                    account_choice = partial[0].account_id
                    break
                elif len(partial) > 1:
                    print('multiple accounts match that name, please be more specific or use index:')
                    for a in partial:
                        print('-', a.name)
                    continue
                else:
                    print('invalid input, no matching account found; try again or press Enter to cancel')
                    continue

            # if user cancelled, go back to main prompt
            if not account_choice:
                continue

            # category optional
            cats = cs.list_categories()
            category_choice = None
            if cats:
                print('Choose category to filter by (optional):')
                for i, c in enumerate(cats, start=1):
                    print(f"{i}) {c.name}")
                sel_cat = input('category index (optional): ').strip()
                if sel_cat:
                    try:
                        idxc = int(sel_cat)
                        if 1 <= idxc <= len(cats):
                            category_choice = cats[idxc-1].category_id
                        else:
                            print('invalid category selection, ignoring')
                    except Exception:
                        print('invalid category selection, ignoring')

            # date range optional
            s_input = input('start date (YYYY-MM-DD, optional): ').strip()
            e_input = input('end date (YYYY-MM-DD, optional): ').strip()
            if s_input:
                start = parse_date(s_input)
            else:
                start = None
            if e_input:
                end = parse_date(e_input)
            else:
                end = None

            # Build SQL
            sql = "SELECT * FROM records WHERE account_id = ?"
            params = [account_choice]
            if category_choice:
                sql += " AND category_id = ?"
                params.append(category_choice)
            if start and end:
                sql += " AND date BETWEEN ? AND ?"
                params.extend([start.isoformat(), end.isoformat()])
            elif start and not end:
                sql += " AND date >= ?"
                params.append(start.isoformat())
            elif end and not start:
                sql += " AND date <= ?"
                params.append(end.isoformat())
            sql += " ORDER BY date DESC"

            rows = db.query(sql, tuple(params))
            # prepare maps
            cat_map = {c.category_id: c.name for c in cats}
            acc_map = {a.account_id: a.name for a in accs}
            if not rows:
                print('No records found for the given filters.')
            else:
                for idx, r in enumerate(rows, start=1):
                    cname = cat_map.get(r['category_id'], '其他') if r['category_id'] else '其他'
                    aname = acc_map.get(r['account_id'], '未知账户')
                    rec_id = r['record_id'] if 'record_id' in r.keys() else None
                    short_id = (rec_id[:8] + '...') if rec_id else ''
                    print(f"{idx}) {r['date']} {r['type']} {r['amount']} {cname} {aname} {r['note']} {short_id}")
            continue
        if cmd == 'addcat':
            name = input('name: ')
            cat = Category(category_id=str(uuid.uuid4()), name=name)
            cs.add_category(cat)
            print('category added:', cat.name, f"(id={cat.category_id[:8]}...)")
            continue
        if cmd == 'listcat':
            # 显示友好的分类列表：每行只显示分类名字，便于用户阅读
            for c in cs.list_categories():
                print(c.name)
            continue
        if cmd in ('delrec', 'deleterec'):
            # Show recent records for selection
            recent = rs.list_records(10, 0)
            if not recent:
                print('No records available to delete.')
                continue
            print('Recent records:')
            for i, r in enumerate(recent, start=1):
                # build category and account maps for display
                catmap = {c.category_id: c.name for c in cs.list_categories()}
                accmap = {a.account_id: a.name for a in asvc.list_accounts()}
                cname = catmap.get(r.category_id, '其他') if r.category_id else '其他'
                aname = accmap.get(r.account_id, '无账户') if getattr(r, 'account_id', None) else '无账户'
                short_id = (r.record_id[:8] + '...') if getattr(r, 'record_id', None) else ''
                print(f"{i}) {r.date.isoformat()} {r.type.value} {r.amount} {cname} {aname} {r.note} {short_id}")

            sel = input('Choose record index to delete or paste full record_id (Enter to cancel): ').strip()
            if not sel:
                print('cancelled')
                continue
            # determine record_id
            record_id = None
            if sel.isdigit():
                idx = int(sel)
                if 1 <= idx <= len(recent):
                    record_id = recent[idx-1].record_id
                else:
                    print('invalid index')
                    continue
            else:
                record_id = sel

            confirm = input(f"Type YES to permanently delete selected record (id starts with {record_id[:8]}): ").strip()
            if confirm != 'YES':
                print('aborted')
                continue
            ok = rs.delete_record(record_id)
            print('deleted' if ok else 'record not found')
            continue
        if cmd == 'delacct':
            accs = asvc.list_accounts()
            if not accs:
                print('No accounts found.')
                continue
            print('Choose account to delete:')
            for i, a in enumerate(accs, start=1):
                print(f"{i}) {a.name}")
            sel = input('account index: ').strip()
            try:
                idx = int(sel)
                if not (1 <= idx <= len(accs)):
                    print('invalid index')
                    continue
            except Exception:
                print('invalid input')
                continue
            acc = accs[idx-1]
            # check for dependent records
            cnt = db.query('SELECT COUNT(1) as c FROM records WHERE account_id=?', (acc.account_id,))[0][0]
            if cnt and cnt > 0:
                print(f'Account has {cnt} records. Use force to delete account and its records.')
                force = input('Type YES to force delete (will remove related records): ').strip() == 'YES'
            else:
                force = False
            confirm = input(f"Type YES to delete account '{acc.name}': ").strip()
            if confirm != 'YES':
                print('aborted')
                continue
            ok = asvc.delete_account(acc.account_id, force=force)
            print('deleted' if ok else 'cannot delete account (has dependent records)')
            continue
        if cmd == 'delcat':
            cats = cs.list_categories()
            if not cats:
                print('No categories found.')
                continue
            print('Choose category to delete:')
            for i, c in enumerate(cats, start=1):
                print(f"{i}) {c.name}")
            sel = input('category index: ').strip()
            try:
                idx = int(sel)
                if not (1 <= idx <= len(cats)):
                    print('invalid index')
                    continue
            except Exception:
                print('invalid input')
                continue
            cat = cats[idx-1]
            # protect built-in category '其他' from deletion
            if getattr(cat, 'name', '') == '其他':
                print("Cannot delete built-in category '其他'.")
                continue
            cnt = db.query('SELECT COUNT(1) as c FROM records WHERE category_id=?', (cat.category_id,))[0][0]
            if cnt and cnt > 0:
                print(f'Category has {cnt} records. Force will detach records (set to uncategorized) and delete category.')
                force = input('Type YES to force (detach records and delete): ').strip() == 'YES'
            else:
                force = False
            confirm = input(f"Type YES to delete category '{cat.name}': ").strip()
            if confirm != 'YES':
                print('aborted')
                continue
            ok = cs.delete_category(cat.category_id, force=force)
            print('deleted' if ok else 'cannot delete category (has dependent records)')
            continue
        if cmd == 'reset':
            print('WARNING: this will delete ALL user data (records, accounts, categories, budgets, notifications)')
            confirm = input("Type YES to proceed and create a backup: ").strip()
            if confirm != 'YES':
                print('aborted')
                continue
            # create backup first
            import time
            backup_path = str(db.path) + '.backup.' + time.strftime('%Y%m%d%H%M%S')
            try:
                db.backup(backup_path)
                print('backup saved to', backup_path)
            except Exception as e:
                print('backup failed:', e)
                # still proceed only if user re-confirms
                more = input('Backup failed. Type YES to continue without backup: ').strip()
                if more != 'YES':
                    print('aborted')
                    continue
            # delete all rows
            db.execute('DELETE FROM records')
            db.execute('DELETE FROM accounts')
            db.execute('DELETE FROM categories')
            db.execute('DELETE FROM budgets')
            db.execute('DELETE FROM notifications')
            print('database reset complete')
            continue
        print('unknown command')

    db.close()


if __name__ == '__main__':
    run_cli()
