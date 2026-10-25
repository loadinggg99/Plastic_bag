# app/server/sections.py
"""六个调研板块的元数据、解析与安全渲染。

这个模块只做三件事：
1. 定义六个板块（标题、简介、按钮用的 SVG 图标）；
2. 把 Agent 返回的整段文本按【板块名】拆成 intro + 六个 section；
3. 把板块正文渲染成 HTML（转义 + 链接白名单），供 Jinja2 详情页直接输出。

注意：这里不信任任何模型输出。所有动态文本都先 escape，再拼接我们自己的
HTML 标签；URL 只允许 http(s)，因此不会产生 XSS。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from markupsafe import Markup, escape


# ---------------------------------------------------------------------------
# 六个板块
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Domain:
    key: str
    title: str
    description: str
    icon: Markup


def _icon(inner: str) -> Markup:
    """把 SVG 内部路径包成 Markup；图标是代码里的静态常量，不放用户输入。"""
    return Markup(inner)


DOMAINS: tuple[Domain, ...] = (
    Domain(
        key="basic",
        title="基础工商信息",
        description="企业名称、各类代码、法定代表人、注册资本、经营状态与注册地址",
        icon=_icon(
            '<path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"/>'
            '<path d="M16 9h2a2 2 0 0 1 2 2v10"/>'
            '<path d="M2 21h20"/>'
            '<path d="M8 7h4M8 11h4M8 15h4"/>'
        ),
    ),
    Domain(
        key="equity",
        title="人员与股权结构",
        description="主要人员、股东、最终受益人、实际控制人与股权穿透关系",
        icon=_icon(
            '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
            '<circle cx="9" cy="7" r="4"/>'
            '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
            '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
        ),
    ),
    Domain(
        key="finance",
        title="经营与财务状况",
        description="财务数据、上市信息、对外投资、融资历史、企业年报与招投标",
        icon=_icon(
            '<path d="M3 3v18h18"/>'
            '<path d="M7 15l4-4 3 3 5-6"/>'
            '<path d="M19 8h-4"/>'
            '<path d="M19 8v4"/>'
        ),
    ),
    Domain(
        key="risk",
        title="风险与司法信息",
        description="司法风险、执行信息、经营异常、税务风险与破产重整",
        icon=_icon(
            '<path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z"/>'
            '<path d="M12 8v4"/>'
            '<path d="M12 16h.01"/>'
        ),
    ),
    Domain(
        key="ip",
        title="知识产权与资质",
        description="商标、专利、著作权、软件著作权、资质证书与网站备案",
        icon=_icon(
            '<circle cx="12" cy="9" r="5"/>'
            '<path d="M9 13.5L8 21l4-2 4 2-1-7.5"/>'
        ),
    ),
    Domain(
        key="opinion",
        title="经营状况与舆情",
        description="员工规模、招聘信息、新闻舆情与企业评分",
        icon=_icon(
            '<path d="M4 5h13a2 2 0 0 1 2 2v12H6a2 2 0 0 1-2-2V5z"/>'
            '<path d="M19 9h1a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-1"/>'
            '<path d="M8 9h5M8 13h5M8 17h3"/>'
        ),
    ),
)

DOMAIN_BY_KEY = {domain.key: domain for domain in DOMAINS}
DOMAIN_BY_TITLE = {domain.title: domain for domain in DOMAINS}

FALLBACK_ICON = _icon(
    '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
    '<path d="M14 2v6h6"/>'
    '<path d="M8 13h8M8 17h8"/>'
)


# ---------------------------------------------------------------------------
# 从 Agent 输出里拆分六个板块
# ---------------------------------------------------------------------------
_BRACKET_RE = re.compile(r"^【(.+?)】\s*(.*)$")
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
_BOLD_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")

_NUMBERING_RES = (
    re.compile(r"^[（(][一二三四五六七八九十百]+[）)]\s*"),
    re.compile(r"^[一二三四五六七八九十百]+[、.．]\s*"),
    re.compile(r"^\d+[、.．)]\s*"),
)


@dataclass
class ParsedReport:
    intro: str
    sections: dict[str, str]
    fallback: str


def _normalize_title(raw: str) -> str:
    title = str(raw).strip()
    title = re.sub(r"^【\s*", "", title)
    title = re.sub(r"\s*】$", "", title)
    for pattern in _NUMBERING_RES:
        title = pattern.sub("", title)
    title = re.sub(r"[：:]\s*$", "", title)
    return title.strip()


def match_domain(line: str) -> tuple[Domain, str] | None:
    """匹配一行是不是板块标题；返回 (板块, 同一行剩余的正文)。"""
    text = line.strip()

    bracket = _BRACKET_RE.match(text)
    if bracket:
        domain = DOMAIN_BY_TITLE.get(_normalize_title(bracket.group(1)))
        if domain:
            return domain, bracket.group(2)

    heading = _HEADING_RE.match(text)
    if heading:
        domain = DOMAIN_BY_TITLE.get(_normalize_title(heading.group(1)))
        if domain:
            return domain, ""

    bold = _BOLD_RE.match(text)
    if bold:
        domain = DOMAIN_BY_TITLE.get(_normalize_title(bold.group(1)))
        if domain:
            return domain, ""

    domain = DOMAIN_BY_TITLE.get(_normalize_title(text))
    if domain:
        return domain, ""
    return None


def _trim_blank_lines(lines: list[str]) -> list[str]:
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def parse_report(text: str) -> ParsedReport:
    """把 Agent 的整段输出拆成前言 + 六个板块正文。

    - 六个板块标题支持【板块名】、Markdown 标题、整行加粗、带编号等写法；
    - 正文里的【备注】之类不会被误拆；
    - 一个板块都没识别出来时，整段放进 fallback，报告页会提供“完整内容”入口。
    """
    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    intro_lines: list[str] = []
    grouped: dict[str, list[str]] = {}
    current: Domain | None = None

    for line in lines:
        matched = match_domain(line)
        if matched is not None:
            current, rest = matched
            grouped.setdefault(current.key, [])
            if rest:
                grouped[current.key].append(rest)
        elif current is not None:
            grouped[current.key].append(line)
        else:
            intro_lines.append(line)

    sections: dict[str, str] = {}
    for domain in DOMAINS:
        body_lines = grouped.get(domain.key)
        if body_lines is None:
            continue
        body = "\n".join(_trim_blank_lines(body_lines)).strip()
        if body:
            sections[domain.key] = body

    if not sections:
        return ParsedReport(intro="", sections={}, fallback=normalized.strip())

    intro = "\n".join(_trim_blank_lines(intro_lines)).strip()
    return ParsedReport(intro=intro, sections=sections, fallback="")


# ---------------------------------------------------------------------------
# 板块正文 -> 安全 HTML
# ---------------------------------------------------------------------------
_URL_RE = re.compile(r"https?://[^\s<>\"'）】》，。；：！？、]+")
_TRAILING_PUNCT = ".,;:!?"


def _safe_http_url(url: str) -> str | None:
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        return None
    return url


def _linkify(raw: str) -> Markup:
    """转义整段文本，只把合法的 http(s) URL 变成链接。"""
    out: list[Markup] = []
    position = 0

    for match in _URL_RE.finditer(raw):
        out.append(escape(raw[position:match.start()]))

        token = match.group(0)
        url = token.rstrip(_TRAILING_PUNCT)
        tail = token[len(url):]

        if _safe_http_url(url):
            href = escape(url)
            out.append(
                Markup(
                    f'<a href="{href}" target="_blank" rel="noopener noreferrer nofollow" '
                    f'referrerpolicy="no-referrer">{escape(url)}</a>'
                )
            )
        else:
            out.append(escape(url))
        if tail:
            out.append(escape(tail))
        position = match.end()

    out.append(escape(raw[position:]))
    return Markup("").join(out)


def _split_table_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]

    cells: list[str] = []
    current = ""
    index = 0
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text) and text[index + 1] == "|":
            current += "|"
            index += 2
            continue
        if text[index] == "|":
            cells.append(current.strip())
            current = ""
            index += 1
            continue
        current += text[index]
        index += 1
    cells.append(current.strip())
    return cells


def _is_table_separator(line: str) -> bool:
    text = line.strip()
    if "|" not in text or "-" not in text:
        return False
    cells = _split_table_row(text)
    return bool(cells) and all(re.fullmatch(r":?-+:?", cell.strip()) for cell in cells)


def _cell_align(cell: str) -> str:
    text = cell.strip()
    left = text.startswith(":")
    right = text.endswith(":")
    if left and right:
        return "is-center"
    if right:
        return "is-right"
    if left:
        return "is-left"
    return ""


def _render_table(header: list[str], aligns: list[str], rows: list[list[str]]) -> Markup:
    parts: list[Markup] = [Markup('<div class="table-wrap"><table><thead><tr>')]
    for idx, cell in enumerate(header):
        cls = f' class="{aligns[idx]}"' if idx < len(aligns) and aligns[idx] else ""
        parts.append(Markup(f"<th{cls}>{_linkify(cell)}</th>"))
    parts.append(Markup("</tr></thead><tbody>"))
    for row in rows:
        parts.append(Markup("<tr>"))
        for idx in range(len(header)):
            cell = row[idx] if idx < len(row) else ""
            cls = f' class="{aligns[idx]}"' if idx < len(aligns) and aligns[idx] else ""
            parts.append(Markup(f"<td{cls}>{_linkify(cell)}</td>"))
        parts.append(Markup("</tr>"))
    parts.append(Markup("</tbody></table></div>"))
    return Markup("").join(parts)


def render_section_html(text: str) -> Markup:
    """把板块正文渲染成 HTML：字段行、列表、表格、小标题都做安全转义。"""
    lines = str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    parts: list[Markup] = []
    list_items: list[Markup] = []

    def flush_list() -> None:
        if not list_items:
            return
        items = Markup("").join(
            Markup(f"<li>{item}</li>") for item in list_items
        )
        parts.append(Markup(f'<ul class="section-list">{items}</ul>'))
        list_items.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            flush_list()
            index += 1
            continue

        # GFM 表格：表头 + |---|---| + 数据行
        if "|" in stripped and index + 1 < len(lines) and _is_table_separator(lines[index + 1]):
            flush_list()
            header = _split_table_row(stripped)
            aligns = [_cell_align(cell) for cell in _split_table_row(lines[index + 1])]
            rows: list[list[str]] = []
            index += 2
            while index < len(lines):
                row_line = lines[index].strip()
                if not row_line or "|" not in row_line or _is_table_separator(row_line):
                    break
                rows.append(_split_table_row(row_line))
                index += 1
            parts.append(_render_table(header, aligns, rows))
            continue

        bracket = _BRACKET_RE.match(stripped)
        if bracket and bracket.group(2) == "":
            flush_list()
            parts.append(
                Markup(f'<h2 class="section-subtitle">{escape(bracket.group(1))}</h2>')
            )
            index += 1
            continue

        heading = _HEADING_RE.match(stripped)
        if heading:
            flush_list()
            parts.append(
                Markup(f'<h2 class="section-subtitle">{escape(heading.group(1))}</h2>')
            )
            index += 1
            continue

        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        if bullet:
            list_items.append(_linkify(bullet.group(1)))
            index += 1
            continue

        flush_list()

        # 单独一行的 URL 不要被当成 "https: //..." 字段
        if re.match(r"^https?://", stripped):
            parts.append(Markup(f'<p class="section-text">{_linkify(stripped)}</p>'))
            index += 1
            continue

        field = re.match(r"^([^：:]{1,20})[：:]\s*(.*)$", stripped)
        if field:
            label = field.group(1).strip()
            value = field.group(2).strip()
            parts.append(
                Markup(
                    f'<div class="field"><span class="field__label">{escape(label)}</span>'
                    f'<span class="field__sep">：</span>'
                    f'<span class="field__value">{_linkify(value)}</span></div>'
                )
            )
        else:
            parts.append(Markup(f'<p class="section-text">{_linkify(stripped)}</p>'))
        index += 1

    flush_list()

    if not parts:
        return Markup('<p class="section-empty">本次未返回该板块内容。</p>')
    return Markup("").join(parts)
