"""单元测试：验证存储和命令行逻辑是否正确。

运行方式：
    python -m unittest test_todo -v
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from storage import Task, TaskStore
from todo import (add_task, delete_task, done_task, clear_tasks,
                  search_tasks, edit_task, filter_tasks, build_parser)


class FakeArgs:
    """模拟 argparse 解析出的参数对象。"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestTaskStore(unittest.TestCase):
    """测试存储模块。"""

    def setUp(self):
        # 每个测试用独立的临时文件，互不干扰
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "tasks.json"
        self.store = TaskStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_empty(self):
        """文件不存在时返回空列表。"""
        self.assertEqual(self.store.load(), [])

    def test_save_and_load_roundtrip(self):
        """保存后再读取，数据应一致。"""
        tasks = [Task(id=1, title="写作业", priority="high", due="2026-09-20")]
        self.store.save(tasks)
        loaded = self.store.load()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].title, "写作业")
        self.assertEqual(loaded[0].priority, "high")

    def test_next_id(self):
        """空列表下一个编号应为 1。"""
        self.assertEqual(self.store.next_id([]), 1)
        self.assertEqual(self.store.next_id([Task(id=3, title="x")]), 4)


class TestCommands(unittest.TestCase):
    """测试各条命令的行为。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = TaskStore(Path(self.tmp.name) / "tasks.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_task(self):
        add_task(FakeArgs(title="买牛奶", priority="high", due="2026-09-20"),
                 self.store)
        tasks = self.store.load()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "买牛奶")

    def test_done_task(self):
        add_task(FakeArgs(title="买牛奶", priority="medium", due=None), self.store)
        tid = self.store.load()[0].id
        done_task(FakeArgs(id=tid), self.store)
        self.assertTrue(self.store.load()[0].done)

    def test_delete_task(self):
        add_task(FakeArgs(title="买牛奶", priority="medium", due=None), self.store)
        tid = self.store.load()[0].id
        delete_task(FakeArgs(id=tid), self.store)
        self.assertEqual(self.store.load(), [])

    def test_clear_completed(self):
        add_task(FakeArgs(title="任务A", priority="medium", due=None), self.store)
        add_task(FakeArgs(title="任务B", priority="medium", due=None), self.store)
        tasks = self.store.load()
        tasks[0].done = True
        self.store.save(tasks)
        clear_tasks(FakeArgs(), self.store)
        remaining = self.store.load()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].title, "任务B")

    def test_search(self):
        add_task(FakeArgs(title="买牛奶", priority="medium", due=None), self.store)
        add_task(FakeArgs(title="写作业", priority="medium", due=None), self.store)
        hits = [t for t in self.store.load() if "牛奶" in t.title]
        self.assertEqual(len(hits), 1)

    def test_edit_task(self):
        """编辑任务应更新标题、优先级和截止日期。"""
        add_task(FakeArgs(title="买牛奶", priority="medium", due=None), self.store)
        tid = self.store.load()[0].id
        edit_task(FakeArgs(id=tid, title="买两盒牛奶", priority="high",
                           due="2026-09-30"), self.store)
        t = self.store.load()[0]
        self.assertEqual(t.title, "买两盒牛奶")
        self.assertEqual(t.priority, "high")
        self.assertEqual(t.due, "2026-09-30")

    def test_filter_tasks(self):
        """筛选函数应按优先级和完成状态正确过滤。"""
        add_task(FakeArgs(title="任务A", priority="high", due=None), self.store)
        add_task(FakeArgs(title="任务B", priority="low", due=None), self.store)
        tasks = self.store.load()
        tasks[0].done = True
        self.store.save(tasks)

        highs = filter_tasks(self.store.load(), priority="high")
        self.assertEqual(len(highs), 1)
        self.assertEqual(highs[0].title, "任务A")

        pendings = filter_tasks(self.store.load(), done=False)
        self.assertEqual(len(pendings), 1)
        self.assertEqual(pendings[0].title, "任务B")


if __name__ == "__main__":
    unittest.main()
