# todo-cli

一个用 Python 编写的轻量级待办清单命令行工具。支持添加、查看、完成、删除、搜索任务，数据自动保存到本地 JSON 文件。

## 功能特性

- ✅ 增删改查任务，支持优先级（high / medium / low）和截止日期
- 📝 编辑任务：修改标题、优先级、截止日期
- 🔎 按状态（待办 / 已完成）和优先级筛选任务
- 💾 数据持久化到 JSON 文件，重启不丢失
- 🔍 按关键字搜索任务
- 📊 任务统计：完成率、优先级分布
- 🧹 一键清理已完成任务
- 🧪 完整的单元测试覆盖核心逻辑

## 环境要求

- Python 3.9+（仅使用标准库，无需安装第三方依赖）

## 快速开始

```bash
# 添加任务（-p 优先级，-d 截止日期）
python todo.py add "买牛奶" -p high -d 2026-09-20

# 查看所有任务
python todo.py list

# 只看未完成的高优先级任务
python todo.py list --pending -p high

# 编辑任务 1（-t 标题，-p 优先级）
python todo.py edit 1 -t "买两盒牛奶" -p high

# 标记任务 1 为完成
python todo.py done 1

# 删除任务 1
python todo.py delete 1

# 搜索包含"牛奶"的任务
python todo.py search 牛奶

# 查看任务统计
python todo.py stats

# 清理所有已完成任务
python todo.py clear
```

### 参数速查

| 短参数 | 长参数 | 作用 |
|---|---|---|
| `-p` | `--priority` | 优先级（high / medium / low） |
| `-d` | `--due` | 截止日期（YYYY-MM-DD） |
| `-t` | `--title` | 任务内容（`edit` 命令用） |

### 哪里可以替换

命令里这些部分是示例，换成你自己的内容：

| 示例里写的 | 换成什么 |
|---|---|
| `"买牛奶"` | 你的任务内容 |
| `1` | 任务编号（`list` 里 `#` 后面的数字） |
| `high` | `high` / `medium` / `low` 三选一 |
| `2026-09-20` | 你的截止日期 |

## 数据存储

任务数据默认保存到 `D:\项目\data\todo\tasks.json`，可用环境变量 `DATA_DIR` 更改存储根目录（默认 `D:/项目/data`）：

```bash
# 想换位置时设置（临时生效）
set DATA_DIR=D:/我的数据
```

## 运行测试

```bash
python -m unittest test_todo -v
```

## 项目结构

```
todo-cli/
├── todo.py          # 主程序：命令行入口 + 各命令逻辑
├── storage.py       # 数据层：Task 模型 + JSON 读写
├── test_todo.py     # 单元测试
└── README.md
```

## 设计说明

项目采用「数据层 / 逻辑层」分离的结构：

- `storage.py` 只负责「数据怎么存」——定义 `Task` 数据结构和 `TaskStore` 读写类。
- `todo.py` 只负责「程序做什么」——用 `argparse` 解析命令，再调用存储层。

这样做的好处是：以后想把 JSON 换成 SQLite 或数据库，只需修改 `storage.py` 一个文件，业务逻辑无需改动。

此外，筛选逻辑被抽成了纯函数 `filter_tasks()`（不依赖任何外部状态），这样它可以直接被单元测试调用，不必模拟命令行交互。
