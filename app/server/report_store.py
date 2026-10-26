"""进程内报告缓存（TTL + 容量上限）。

/api/query 写入，报告页与详情页按 report_id 读取；过期后由用户重新查询。
单进程内存实现：多 worker / 多实例部署时需替换为 Redis 等共享存储。
"""
from __future__ import annotations

import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass

from server.config import settings

from agent.logger import get_logger

logger = get_logger("server.report_store")


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
        if expired:
            logger.info("清理过期报告 %d 份，剩余 %d 份", len(expired), len(self._items))

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
            logger.info(
                "缓存报告：id=%s 公司=%r 板块=%d 前言=%d字 fallback=%s 当前缓存=%d 份",
                report.id,
                company,
                len(sections),
                len(intro),
                bool(fallback),
                len(self._items),
            )
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
