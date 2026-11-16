import re
from functools import lru_cache

from PyQt6.QtWebEngineCore import (
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)

from monobrowser import session
from monobrowser.utils import assets_path

ADBLOCK_HOSTS_PATH = assets_path("hosts.txt")

_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)([a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?\.)+[a-z0-9-]{2,63}$"
)


@lru_cache(maxsize=1)
def blocked_domains() -> frozenset[str]:
    domains: set[str] = set()
    try:
        text = ADBLOCK_HOSTS_PATH.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return frozenset()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        host = parts[-1].lower().rstrip(".")
        if _DOMAIN_RE.match(host):
            domains.add(host)
    return frozenset(domains)


def is_blocked(host: str) -> bool:
    host = host.lower().rstrip(".")
    if not host:
        return False
    blocked = blocked_domains()
    while True:
        if host in blocked:
            return True
        dot = host.find(".")
        if dot == -1:
            return False
        host = host[dot + 1 :]


_blocked_count = 0


def blocked_count() -> int:
    return _blocked_count


class AdblockInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        global _blocked_count
        if not session.adblock_enabled():
            return
        host = info.requestUrl().host()
        if host and is_blocked(host):
            _blocked_count += 1
            info.block(True)
