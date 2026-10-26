# app/server/report_store.py
"""进程内报告缓存。

`/api/query` 生成报告后写进这里，`/report/{id}` 与 `/report/{id}/{section}`
再从缓存读取。报告不是长期数据，过期后让用户重新查询即可。

注意：这是单进程内存缓存。如果以后用多 worker / 多实例部署，需要换成
Redis、SQLite 之类的共享存储，否则详情页可能落到没有该报告的进程。
"""
from __future__ import annotations

import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass

from server.config import settings


@dataclass
class StoredReport:
    id: str
    company: str
    raw: str
    intro: str
    sections: dict[str, str]
    fallback: str
    created_at: float


class ReportStore:
    """带 TTL 和容量上限的线程安全报告缓存。"""

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 200) -> None:
        self._ttl = max(0, int(ttl_seconds))
        self._max_entries = max(1, int(max_entries))
        self._lock = threading.Lock()
        self._items: OrderedDict[str, StoredReport] = OrderedDict()

    def _purge_locked(self, now: float) -> None:
        expired = [
            report_id
            for report_id, report in self._items.items()
            if now - report.created_at >= self._ttl
        ]
        for report_id in expired:
            self._items.pop(report_id, None)

    def put(
        self,
        *,
        company: str,
        raw: str,
        intro: str,
        sections: dict[str, str],
        fallback: str,
    ) -> StoredReport:
        with self._lock:
            now = time.monotonic()
            self._purge_locked(now)

            report_id = uuid.uuid4().hex[:12]
            while report_id in self._items:
                report_id = uuid.uuid4().hex[:12]

            report = StoredReport(
                id=report_id,
                company=company,
                raw=raw,
                intro=intro,
                sections=dict(sections),
                fallback=fallback,
                created_at=now,
            )
            self._items[report_id] = report
            while len(self._items) > self._max_entries:
                self._items.popitem(last=False)
            return report

    def get(self, report_id: str) -> StoredReport | None:
        with self._lock:
            now = time.monotonic()
            self._purge_locked(now)
            report = self._items.get(report_id)
            if report is None:
                return None
            self._items.move_to_end(report_id)
            return report

    def clear(self) -> None:
        """测试或运维用：清空缓存。"""
        with self._lock:
            self._items.clear()


report_store = ReportStore(
    ttl_seconds=settings.report_ttl_seconds,
    max_entries=settings.report_max_entries,
)
