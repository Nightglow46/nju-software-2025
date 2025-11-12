from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid
from datetime import date, datetime


class RecordType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass
class Category:
    category_id: str
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None


@dataclass
class Account:
    account_id: str
    name: str
    type: Optional[str] = None
    balance: float = 0.0
    currency: str = 'CNY'


@dataclass
class Budget:
    budget_id: str
    category_id: Optional[str]
    limit: float
    period: str  # e.g., 'monthly', 'weekly'


@dataclass
class Notification:
    notif_id: str
    type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Record:
    """表示一条收支记录。

    字段说明：
    - record_id: 唯一标识符 (UUID 字符串)
    - amount: 金额，收入为正，支出为正（类型字段区分）
    - type: RecordType 枚举，INCOME 或 EXPENSE
    - date: 记录发生日期
    - category_id: 可选的分类 id（与 Category 表关联）
    - tags: 字符串标签列表，方便搜索
    - note: 备注
    - attachments: 附件路径列表（未来可集成文件存储）
    """

    record_id: str
    amount: float
    type: RecordType
    date: date
    category_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    note: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    account_id: Optional[str] = None

    @staticmethod
    def create(amount: float, rtype: RecordType, date_obj: date, category_id: Optional[str] = None,
               tags: Optional[List[str]] = None, note: Optional[str] = None,
               attachments: Optional[List[str]] = None,
               account_id: Optional[str] = None) -> 'Record':
        """创建并返回一个 Record 实例，自动生成 UUID。"""
        # 这里使用 uuid4 生成唯一 id，以便无需集中式 id 管理
        return Record(
            record_id=str(uuid.uuid4()),
            amount=amount,
            type=rtype,
            date=date_obj,
            category_id=category_id,
            tags=tags or [],
            note=note,
            attachments=attachments or [],
            account_id=account_id,
        )

