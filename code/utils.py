from datetime import datetime, date
from typing import Optional


def parse_date(s: Optional[str]) -> date:
    if not s:
        return date.today()
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return datetime.strptime(s, "%Y-%m-%d").date()


def format_currency(amount: float, currency: str = 'CNY') -> str:
    """简单格式化货币显示。未来可以扩展国际化支持。"""
    # 这里不引入 babel 等库以保持依赖最小
    return f"{currency} {amount:.2f}"

