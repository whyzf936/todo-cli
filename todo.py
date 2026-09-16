"""待办清单命令行工具。

用法示例：
    python todo.py add "买牛奶" --priority high --due 2026-09-20
    python todo.py list
    python todo.py list --pending --priority high
    python todo.py edit 1 --title "买两盒牛奶" --priority high
    python todo.py done 1
    python todo.py delete 2
    python todo.py clear
    python todo.py search 牛奶
    python todo.py stats
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from storage import Task, TaskStore

# Windows 控制台默认使用 GBK 编码，输出中文/emoji 会报 UnicodeEncodeError；
# 这里把标准输出/错误流切换到 UTF-8，保证跨平台正常显示。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# 优先级排序权重：数字越小越靠前
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def add_task(args: argparse.Namespace, store: TaskStore) -> None:
    """添加一条任务。"""
    tasks = store.load()
    task = Task(
        id=store.next_id(tasks),
        title=args.title,
        priority=args.priority,
        due=args.due,
    )
    tasks.append(task)
    store.save(tasks)
    print(f"✅ 已添加任务 #{task.id}: {task.title}")


def filter_tasks(tasks: list[Task], done: Optional[bool] = None,
                 priority: Optional[str] = None) -> list[Task]:
    """按完成状态和优先级筛选任务（纯函数，方便单元测试）。

    done=None 表示不按状态筛选；priority=None 表示不按优先级筛选。
    """
    if done is not None:
        tasks = [t for t in tasks if t.done == done]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    return tasks


def list_tasks(args: argparse.Namespace, store: TaskStore) -> None:
    """列出任务：未完成在前，按优先级排序，支持筛选。"""
    tasks = store.load()
    # 把 --pending / --done 两个互斥参数统一成一个 done 值
    done = True if args.done else (False if args.pending else None)
    tasks = filter_tasks(tasks, done=done, priority=args.priority)

    if not tasks:
        print("📭 没有符合条件的任务")
        return
    tasks.sort(key=lambda t: (t.done, PRIORITY_ORDER.get(t.priority, 1), t.id))
    for t in tasks:
        mark = "✅" if t.done else "⬜"
        due = f"  截止:{t.due}" if t.due else ""
        print(f"{mark} #{t.id} [{t.priority}] {t.title}{due}")


def edit_task(args: argparse.Namespace, store: TaskStore) -> None:
    """编辑指定任务的标题 / 优先级 / 截止日期。"""
    tasks = store.load()
    for t in tasks:
        if t.id == args.id:
            if args.title:
                t.title = args.title
            if args.priority:
                t.priority = args.priority
            if args.due:
                t.due = args.due
            store.save(tasks)
            print(f"✏️  已更新任务 #{t.id}: {t.title}")
            return
    print(f"❌ 找不到编号为 {args.id} 的任务", file=sys.stderr)


def done_task(args: argparse.Namespace, store: TaskStore) -> None:
    """把指定编号的任务标记为完成。"""
    tasks = store.load()
    for t in tasks:
        if t.id == args.id:
            t.done = True
            store.save(tasks)
            print(f"🎉 已完成任务 #{t.id}: {t.title}")
            return
    print(f"❌ 找不到编号为 {args.id} 的任务", file=sys.stderr)


def delete_task(args: argparse.Namespace, store: TaskStore) -> None:
    """删除指定编号的任务。"""
    tasks = store.load()
    remaining = [t for t in tasks if t.id != args.id]
    if len(remaining) == len(tasks):
        print(f"❌ 找不到编号为 {args.id} 的任务")
        return
    store.save(remaining)
    print(f"🗑️  已删除任务 #{args.id}")


def clear_tasks(args: argparse.Namespace, store: TaskStore) -> None:
    """清空所有已完成的任务。"""
    tasks = store.load()
    remaining = [t for t in tasks if not t.done]
    removed = len(tasks) - len(remaining)
    store.save(remaining)
    print(f"🧹 已清理 {removed} 条已完成任务")


def search_tasks(args: argparse.Namespace, store: TaskStore) -> None:
    """按关键字搜索任务标题。"""
    tasks = store.load()
    keyword = args.keyword
    hits = [t for t in tasks if keyword in t.title]
    if not hits:
        print(f"🔍 没有找到包含「{keyword}」的任务")
        return
    for t in hits:
        mark = "✅" if t.done else "⬜"
        print(f"{mark} #{t.id} [{t.priority}] {t.title}")


def show_stats(args: argparse.Namespace, store: TaskStore) -> None:
    """统计任务的完成情况和优先级分布。"""
    tasks = store.load()
    total = len(tasks)
    done = sum(1 for t in tasks if t.done)
    pending = total - done
    rate = (done / total * 100) if total else 0.0

    print("📊 任务统计")
    print(f"   总数:   {total}")
    print(f"   已完成: {done}")
    print(f"   未完成: {pending}")
    print(f"   完成率: {rate:.1f}%")
    if total:
        print("   优先级分布:")
        for level in ("high", "medium", "low"):
            count = sum(1 for t in tasks if t.priority == level)
            print(f"      {level:<6} {count}")


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="todo",
        description="一个简单实用的待办清单命令行工具",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加任务")
    p_add.add_argument("title", help="任务内容")
    p_add.add_argument("-p", "--priority", choices=["high", "medium", "low"],
                       default="medium", help="优先级")
    p_add.add_argument("-d", "--due", help="截止日期，格式 YYYY-MM-DD")
    p_add.set_defaults(func=add_task)

    p_list = sub.add_parser("list", help="列出所有任务")
    _status = p_list.add_mutually_exclusive_group()
    _status.add_argument("--pending", action="store_true", help="只显示未完成")
    _status.add_argument("--done", action="store_true", help="只显示已完成")
    p_list.add_argument("-p", "--priority", choices=["high", "medium", "low"],
                        help="按优先级筛选")
    p_list.set_defaults(func=list_tasks)

    p_edit = sub.add_parser("edit", help="编辑任务")
    p_edit.add_argument("id", type=int, help="任务编号")
    p_edit.add_argument("-t", "--title", help="新的任务内容")
    p_edit.add_argument("-p", "--priority", choices=["high", "medium", "low"],
                        help="新的优先级")
    p_edit.add_argument("-d", "--due", help="新的截止日期 YYYY-MM-DD")
    p_edit.set_defaults(func=edit_task)

    p_done = sub.add_parser("done", help="标记任务为完成")
    p_done.add_argument("id", type=int, help="任务编号")
    p_done.set_defaults(func=done_task)

    p_del = sub.add_parser("delete", help="删除任务")
    p_del.add_argument("id", type=int, help="任务编号")
    p_del.set_defaults(func=delete_task)

    sub.add_parser("clear", help="清理已完成任务").set_defaults(func=clear_tasks)

    p_search = sub.add_parser("search", help="按关键字搜索任务")
    p_search.add_argument("keyword", help="搜索关键字")
    p_search.set_defaults(func=search_tasks)

    sub.add_parser("stats", help="查看任务统计").set_defaults(func=show_stats)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    store = TaskStore()
    args.func(args, store)


if __name__ == "__main__":
    main()
