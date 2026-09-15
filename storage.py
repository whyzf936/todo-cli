"""数据存储模块：负责待办任务的读写与持久化。

把「数据怎么存」和「程序逻辑」分开，是好的项目结构习惯。
这样以后想把 JSON 换成 SQLite / 数据库，只需改这一个文件。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# 数据根目录：默认 D:/项目/data，可用环境变量 DATA_DIR 覆盖
DATA_DIR = Path(os.environ.get("DATA_DIR", "D:/项目/data"))
DEFAULT_DB_PATH = DATA_DIR / "todo" / "tasks.json"


@dataclass
class Task:
    """一条待办任务。"""

    title: str                     # 任务内容
    priority: str = "medium"       # high / medium / low
    due: Optional[str] = None      # 截止日期，格式 YYYY-MM-DD
    done: bool = False             # 是否已完成
    id: int = 0                    # 唯一编号
    created_at: str = ""           # 创建时间

    def __post_init__(self):
        # dataclass 创建实例后自动调用，用于填充默认创建时间
        if not self.created_at:
            self.created_at = datetime.now().isoformat(timespec="seconds")


class TaskStore:
    """把任务列表读写到 JSON 文件。"""

    def __init__(self, path: Path = DEFAULT_DB_PATH):
        self.path = path

    def load(self) -> list[Task]:
        """从文件读取所有任务；文件不存在时返回空列表。"""
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Task(**item) for item in data]

    def save(self, tasks: list[Task]) -> None:
        """把任务列表写回文件，自动创建所在目录。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                [asdict(t) for t in tasks],
                f,
                ensure_ascii=False,  # 保留中文，不转义
                indent=2,
            )

    def next_id(self, tasks: list[Task]) -> int:
        """生成下一个自增编号。"""
        return max((t.id for t in tasks), default=0) + 1
