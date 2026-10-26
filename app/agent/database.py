"""SQLite checkpointer。

SqliteSaver 持有非托管的 sqlite3.Connection，因此按数据库路径缓存连接，
避免重复 build_agent("Sqlite") 时泄漏文件句柄。
"""
from contextlib import suppress
from pathlib import Path

from agent.config import dbConfig

_sqlite_cache: dict[Path, object] = {}


def init_sqlite():
    """返回（必要时创建）当前配置对应数据库的 SqliteSaver。"""
    import sqlite3

    from langgraph.checkpoint.sqlite import SqliteSaver

    db_path = Path(dbConfig.DATABASE_URI)
    db_path.parent.mkdir(parents=True, exist_ok=True)   # sqlite 不会自动创建父目录

    cached = _sqlite_cache.get(db_path)
    if cached is not None:
        return cached

    connection = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(connection)
    checkpointer.setup()                                # 幂等：内部有 is_setup 标记

    _sqlite_cache[db_path] = checkpointer
    return checkpointer


def close_sqlite() -> None:
    """关闭并清空缓存的连接（测试或模拟进程重启时使用）。"""
    while _sqlite_cache:
        _, checkpointer = _sqlite_cache.popitem()
        with suppress(Exception):   # 关闭失败不影响主流程
            checkpointer.conn.close()
