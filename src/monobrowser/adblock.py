import re
from dataclasses import dataclass
from functools import lru_cache

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import (
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)

from monobrowser import privacy, session
from monobrowser.utils import assets_path

ADBLOCK_FILTER_PATHS = (
    assets_path("filters/easylist.txt"),
    assets_path("filters/easyprivacy.txt"),
)

_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)([a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?\.)+[a-z0-9-]{2,63}$"
)


@dataclass(frozen=True)
class FilterRule:
    third_party: bool = False
    domains: frozenset[str] = frozenset()
    excluded: frozenset[str] = frozenset()


def _parse_options(options: str) -> FilterRule | None:
    third_party = False
    included: set[str] = set()
    excluded: set[str] = set()
    for option in options.split(","):
        option = option.strip().lower()
        if not option:
            continue
        if option in ("third-party", "3p"):
            third_party = True
            continue
        if option.startswith("domain="):
            for value in option[len("domain=") :].split("|"):
                value = value.strip().lower()
                if not value:
                    continue
                if value.startswith("~"):
                    excluded.add(value[1:])
                else:
                    included.add(value)
            continue
        return None
    return FilterRule(third_party, frozenset(included), frozenset(excluded))


@lru_cache(maxsize=1)
def filter_rules() -> tuple[frozenset[str], dict[str, tuple[FilterRule, ...]]]:
    exceptions: set[str] = set()
    rules: dict[str, list[FilterRule]] = {}
    for path in ADBLOCK_FILTER_PATHS:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith(("!", "[")) or "##" in line or "#@#" in line:
                continue
            negated = line.startswith("@@")
            if negated:
                line = line[2:]
            if not line.startswith("||"):
                continue
            pattern, separator, options = line[2:].partition("$")
            if not pattern.endswith("^"):
                continue
            domain = pattern[:-1].lower().rstrip(".")
            if not _DOMAIN_RE.match(domain):
                continue
            parsed = _parse_options(options) if separator else FilterRule()
            if parsed is None:
                continue
            if negated:
                if parsed == FilterRule():
                    exceptions.add(domain)
                continue
            rules.setdefault(domain, []).append(parsed)
    return frozenset(exceptions), {
        domain: tuple(values) for domain, values in rules.items()
    }


@lru_cache(maxsize=1)
def blocked_domains() -> frozenset[str]:
    _, rules = filter_rules()
    return frozenset(rules)


def rule_count() -> int:
    _, rules = filter_rules()
    return sum(len(values) for values in rules.values())


def _suffixes(host: str) -> list[str]:
    host = host.lower().rstrip(".")
    result: list[str] = []
    while host:
        result.append(host)
        dot = host.find(".")
        if dot == -1:
            break
        host = host[dot + 1 :]
    return result


def _host_matches(host: str, domains: frozenset[str]) -> bool:
    return any(candidate in domains for candidate in _suffixes(host))


def _is_third_party(host: str, first_party: str) -> bool:
    if not first_party:
        return True
    return first_party not in _suffixes(host) and host not in _suffixes(first_party)


def is_blocked(url: str, first_party_url: str = "") -> bool:
    host = QUrl(url).host().lower().rstrip(".")
    if not host:
        return False
    first_party = QUrl(first_party_url).host().lower().rstrip(".")
    exceptions, rules = filter_rules()
    suffixes = _suffixes(host)
    if any(candidate in exceptions for candidate in suffixes):
        return False
    for candidate in suffixes:
        for rule in rules.get(candidate, ()):
            if rule.third_party and not _is_third_party(host, first_party):
                continue
            if rule.domains and not _host_matches(first_party, rule.domains):
                continue
            if rule.excluded and _host_matches(first_party, rule.excluded):
                continue
            return True
    return False


_blocked_count = 0


def blocked_count() -> int:
    return _blocked_count


class AdblockInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        global _blocked_count
        privacy.apply_tracking_headers(info)
        if not session.adblock_enabled():
            return
        url = info.requestUrl()
        first_party = info.firstPartyUrl()
        if is_blocked(url.toString(), first_party.toString()):
            _blocked_count += 1
            info.block(True)
