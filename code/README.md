# 简易记账应用核心（命令行）

主要文件：
- `models.py` - 数据模型（Record, Category, Budget, Notification）
- `db.py` - SQLite 封装
- `services.py` - CRUD 与统计服务
- `cli.py` - 简单交互式命令行

运行：
在 `code` 目录中运行 `python -m cli` 即可启动简单交互。

示例：
1) 添加分类并添加一笔支出
	- python -c "from cli import run_cli; run_cli()" 然后按照提示操作
2) 运行内置检查（无需 pytest）
	- python run_tests_no_pytest.py
