"""SQLite checkpoint 存储。

两个容易踩的点：

1. 目录要自己建。sqlite 不会自动创建父目录，路径不存在时直接
   OperationalError: unable to open database file。

2. 连接要复用。SqliteSaver 持有的 sqlite3.Connection 是非托管资源，
   不会被自动回收。如果每次 build_agent("Sqlite") 都新开一个连接，
   重复调用就会持续泄漏文件句柄。所以这里按数据库路径缓存，
   同一个库只开一个连接；换路径（比如测试用临时目录）才会开新的。
"""
from pathlib import Path

from agent.config import dbConfig

# 按数据库绝对路径缓存 checkpointer，避免重复开连接
_sqlite_cache: dict[Path, object] = {}


def init_sqlite():
    """创建（或复用）SQLite checkpoint 连接。"""
    import sqlite3

    from langgraph.checkpoint.sqlite import SqliteSaver

    db_path = Path(dbConfig.DATABASE_URI)

    # sqlite 不会自动创建目录，所以先确保父目录存在。
    # 数据库落在 app/agent/resources/db/checkpoint.db；首次使用时 db/ 还不存在，
    # 这里会自动建出来（原来写 "./resources/checkpoint.db" 时目录不存在 ->
    # OperationalError: unable to open database file）。
    #
    # 这一步是幂等的：exist_ok=True 时目录已存在就直接返回，不会重复创建、
    # 也不会报错。但如果该路径被同名「文件」占用或没有写权限，依然会抛
    # FileExistsError / PermissionError —— 这是期望行为，不能被静默吞掉。
    db_path.parent.mkdir(parents=True, exist_ok=True)

    cached = _sqlite_cache.get(db_path)
    if cached is not None:
        return cached

    # 创建链接
    connection = sqlite3.connect(
        db_path,
        check_same_thread=False,
    )

    # 初始化
    checkpointer = SqliteSaver(connection)

    # 自动建表（内部有 is_setup 标记，重复调用不会重复建）
    checkpointer.setup()

    # 缓存数据库链接
    _sqlite_cache[db_path] = checkpointer

    return checkpointer


def close_sqlite() -> None:
    """关闭所有缓存的 sqlite 连接。

    进程退出时操作系统会回收句柄，所以正常使用可以不调用；
    测试清理、或者需要在同一个进程里模拟「重启」时用得上。
    """
    while _sqlite_cache:
        # popitem() → 从字典里弹出一个键值对，并从字典中删除它
        _, checkpointer = _sqlite_cache.popitem()
        try:
            checkpointer.conn.close()
        except Exception:  # noqa: BLE001 - 关闭失败不应影响主流程
            pass
