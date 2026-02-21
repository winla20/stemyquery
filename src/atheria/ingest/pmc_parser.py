"""PMC HTML/XML parser for JATS format."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lxml import etree


@dataclass
class ParsedBlock:
    """A parsed block: paragraph, table, caption, etc."""

    block_type: str  # paragraph, table, table_caption, figure_caption
    text: str
    section_path: list[str]
    page: int = 1


@dataclass
class ParsedDocument:
    """Parsed document with structure."""

    title: str
    abstract: str
    blocks: list[ParsedBlock] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_all_text(self) -> str:
        return f"{self.title}\n\n{self.abstract}\n\n" + "\n\n".join(
            b.text for b in self.blocks
        )


def _text_content(el: etree._Element | None) -> str:
    if el is None:
        return ""
    return " ".join(el.itertext()).strip() if hasattr(el, "itertext") else ""


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split()) if text else ""


def _local_tag(el: etree._Element) -> str:
    tag = el.tag
    if not isinstance(tag, str):
        return ""
    if not tag:
        return ""
    return etree.QName(tag).localname if "}" in tag else tag


def _parse_table(table_el: etree._Element) -> str:
    """Extract table as pipe-separated text."""
    rows: list[list[str]] = []
    for tr in table_el.iter():
        if _local_tag(tr) != "tr":
            continue
        row_texts: list[str] = []
        for cell in tr:
            if _local_tag(cell) in ("td", "th"):
                row_texts.append(_normalize_whitespace(_text_content(cell)))
        if row_texts:
            rows.append(row_texts)
    return "\n".join(" | ".join(cell for cell in row) for row in rows)


def _section_title_from_heading(section_el: etree._Element) -> str:
    """Get section title from first h2/h3/h4 child (PMC HTML)."""
    for c in section_el:
        tag = _local_tag(c)
        if tag in ("h2", "h3", "h4", "h5"):
            return _normalize_whitespace(_text_content(c))
    return ""


def _parse_html_section(
    section_el: etree._Element,
    section_path: list[str],
    blocks: list[ParsedBlock],
) -> None:
    """
    Recursively parse PMC HTML section: section_path from h2/h3/h4, then p, table, figure.
    """
    title = _section_title_from_heading(section_el)
    if title:
        section_path = section_path + [title]

    for child in section_el:
        tag = _local_tag(child)
        if tag in ("h2", "h3", "h4", "h5"):
            continue  # already used for section_path
        if tag == "p":
            text = _normalize_whitespace(_text_content(child))
            if text:
                blocks.append(
                    ParsedBlock(
                        block_type="paragraph",
                        text=text,
                        section_path=section_path.copy(),
                        page=1,
                    )
                )
        elif tag == "section":
            # Table wrapper: section with class "tw" (PMC HTML)
            cls = (child.get("class") or "").lower()
            if " tw " in f" {cls} " or cls.strip() == "tw":
                cap_el = None
                for d in child.iter():
                    if "caption" in (d.get("class") or "").lower():
                        cap_el = d
                        break
                if cap_el is not None:
                    cap_text = _normalize_whitespace(_text_content(cap_el))
                    if cap_text:
                        blocks.append(
                            ParsedBlock(
                                block_type="table_caption",
                                text=cap_text,
                                section_path=section_path.copy(),
                                page=1,
                            )
                        )
                table_el = child.find(".//{*}table")
                if table_el is None:
                    table_el = child.find(".//table")
                if table_el is not None:
                    table_text = _parse_table(table_el)
                    if table_text:
                        blocks.append(
                            ParsedBlock(
                                block_type="table",
                                text=table_text,
                                section_path=section_path.copy(),
                                page=1,
                            )
                        )
            else:
                _parse_html_section(child, section_path, blocks)
        elif tag == "figure":
            cap_el = child.find(".//{*}figcaption")
            if cap_el is None:
                cap_el = child.find(".//figcaption")
            if cap_el is not None:
                cap_text = _normalize_whitespace(_text_content(cap_el))
                if cap_text:
                    blocks.append(
                        ParsedBlock(
                            block_type="figure_caption",
                            text=cap_text,
                            section_path=section_path.copy(),
                            page=1,
                        )
                    )
        elif tag == "div" and _local_tag(child) == "div":
            # Skip wrapper divs; content is in section/figure/p
            pass
        elif tag == "table":
            table_text = _parse_table(child)
            if table_text:
                blocks.append(
                    ParsedBlock(
                        block_type="table",
                        text=table_text,
                        section_path=section_path.copy(),
                        page=1,
                    )
                )


def _parse_pmc_html(root: etree._Element, path: Path) -> ParsedDocument | None:
    """
    Parse PMC cloud viewer HTML (article in section.body.main-article-body, section/h2/h3/p/table).
    """
    # Title: meta citation_title or h1 in article
    title = ""
    meta_title = root.find(".//*[@name='citation_title']")
    if meta_title is not None and meta_title.get("content"):
        title = _normalize_whitespace(meta_title.get("content", ""))
    if not title:
        h1 = root.find(".//{*}article//{*}h1") or root.find(".//article//h1")
        if h1 is not None:
            title = _normalize_whitespace(_text_content(h1))

    # Abstract: section.abstract or id=ABS1
    abstract_parts: list[str] = []
    abs_sec = root.find(".//*[@id='ABS1']")
    if abs_sec is None:
        for el in root.iter():
            if "abstract" in (el.get("class") or "").lower():
                abs_sec = el
                break
    if abs_sec is not None:
        for p in abs_sec.iter():
            if _local_tag(p) == "p":
                t = _normalize_whitespace(_text_content(p))
                if t:
                    abstract_parts.append(t)
        if not abstract_parts:
            abstract_parts = [_normalize_whitespace(_text_content(abs_sec))]
    abstract = "\n".join(abstract_parts) if abstract_parts else ""

    # Metadata
    metadata: dict[str, Any] = {}
    meta_pmid = root.find(".//*[@name='citation_pmid']")
    if meta_pmid is not None and meta_pmid.get("content"):
        metadata["pmid"] = meta_pmid.get("content", "").strip()
    # PMC ID from canonical link
    for el in root.iter("link", "a"):
        if el.get("rel") == "canonical" or "pmc" in (el.get("href") or "").lower():
            href = el.get("href") or ""
            m = re.search(r"PMC\d+", href)
            if m:
                metadata["pmc_id"] = m.group(0)
                break

    # Body: use "Article content" container so we get all sections (S2, S5, S6...);
    # the inner "body main-article-body" may be closed early by parser so S5+ are siblings.
    blocks: list[ParsedBlock] = []
    article_content = None
    for el in root.iter():
        if el.get("aria-label") == "Article content":
            article_content = el
            break
    if article_content is None:
        for el in root.iter():
            cls = el.get("class") or ""
            if "main-article-body" in cls:
                article_content = el
                break
    if article_content is not None:
        # PMC HTML can be malformed (e.g. S5 inside a table cell). Collect all sections with id S1, S2, ...
        # in document order; process only "top-level" ones (parent is not another S* section) so we get
        # S2, S5, S6, ... and _parse_html_section recurses into nested S3, S4, S7, etc.
        def is_abstract(s: etree._Element) -> bool:
            sid = s.get("id") or ""
            cls = (s.get("class") or "").lower()
            return sid == "ABS1" or "abstract" in cls

        sid_re = re.compile(r"^S\d+$")
        all_sections: list[etree._Element] = []
        for el in article_content.iter():
            if _local_tag(el) != "section":
                continue
            sid = el.get("id") or ""
            if not sid_re.match(sid) or is_abstract(el):
                continue
            all_sections.append(el)

        def is_top_level(sec: etree._Element) -> bool:
            parent = sec.getparent()
            if parent is None:
                return True
            pid = parent.get("id") or ""
            return not sid_re.match(pid)

        for sec in all_sections:
            if is_top_level(sec):
                _parse_html_section(sec, [], blocks)

    return ParsedDocument(title=title, abstract=abstract, blocks=blocks, metadata=metadata)


def _parse_sec(
    sec_el: etree._Element,
    section_path: list[str],
    blocks: list[ParsedBlock],
) -> int:
    """Recursively parse a section. Returns current page."""
    page = 1

    # Get section title (direct child title)
    title_el = None
    for c in sec_el:
        if _local_tag(c) == "title":
            title_el = c
            break
    if title_el is not None:
        section_path = section_path + [_normalize_whitespace(_text_content(title_el))]

    # Process direct children in order
    for child in sec_el:
        tag = _local_tag(child)
        if tag == "p":
            text = _normalize_whitespace(_text_content(child))
            if text:
                blocks.append(
                    ParsedBlock(
                        block_type="paragraph",
                        text=text,
                        section_path=section_path.copy(),
                        page=page,
                    )
                )
        elif tag == "sec":
            _parse_sec(child, section_path, blocks)
        elif tag == "table-wrap":
            # Caption first
            cap_el = next((c for c in child.iter() if _local_tag(c) == "caption"), None)
            if cap_el is not None:
                cap_text = _normalize_whitespace(_text_content(cap_el))
                if cap_text:
                    blocks.append(
                        ParsedBlock(
                            block_type="table_caption",
                            text=cap_text,
                            section_path=section_path.copy(),
                            page=page,
                        )
                    )
            # Table body
            table_el = next((c for c in child.iter() if _local_tag(c) == "table"), None)
            if table_el is not None:
                table_text = _parse_table(table_el)
                if table_text:
                    blocks.append(
                        ParsedBlock(
                            block_type="table",
                            text=table_text,
                            section_path=section_path.copy(),
                            page=page,
                        )
                    )
        elif tag == "fig":
            cap_el = next((c for c in child.iter() if _local_tag(c) == "caption"), None)
            if cap_el is not None:
                cap_text = _normalize_whitespace(_text_content(cap_el))
                if cap_text:
                    blocks.append(
                        ParsedBlock(
                            block_type="figure_caption",
                            text=cap_text,
                            section_path=section_path.copy(),
                            page=page,
                        )
                    )
        elif tag == "def-list" or tag == "list":
            text = _normalize_whitespace(_text_content(child))
            if text:
                blocks.append(
                    ParsedBlock(
                        block_type="paragraph",
                        text=text,
                        section_path=section_path.copy(),
                        page=page,
                    )
                )

    return page


def parse_pmc(path: str | Path) -> ParsedDocument | None:
    """
    Parse PMC XML/HTML (JATS format) and return structured document.

    Supports:
    - JATS XML (PMC OA)
    - XHTML (PMC HTML)

    Returns None if parsing fails.
    """
    path = Path(path)
    if not path.exists():
        return None

    try:
        parser = etree.XMLParser(recover=True, remove_blank_text=True)
        tree = etree.parse(str(path), parser)
        root = tree.getroot()
    except Exception:
        return None

    ns = root.nsmap or {}
    if None in ns:
        ns[""] = ns.pop(None)

    # PMC cloud viewer HTML: root is <html>, content in section.main-article-body with section/h2/h3/p
    root_tag = _local_tag(root)
    is_html_doc = root_tag == "html" or root.find(".//*[@name='citation_title']") is not None
    if is_html_doc:
        html_doc = _parse_pmc_html(root, path)
        if html_doc is not None and (html_doc.title or html_doc.blocks):
            return html_doc
        # else fall through to JATS path (e.g. XHTML with article/body)

    # Find article (JATS)
    article = root if root.tag.endswith("article") else root.find(".//{*}article") or root

    # Title
    title = ""
    for q in ["article-title", "title"]:
        el = article.find(f".//{{*}}{q}") or article.find(f".//{q}")
        if el is not None:
            title = _normalize_whitespace(_text_content(el))
            if title:
                break

    # Abstract
    abstract_parts: list[str] = []
    abs_el = article.find(".//{*}abstract") or article.find(".//abstract")
    if abs_el is not None:
        for p in abs_el.iter():
            if _local_tag(p) == "p":
                t = _normalize_whitespace(_text_content(p))
                if t:
                    abstract_parts.append(t)
        if not abstract_parts:
            abstract_parts = [_normalize_whitespace(_text_content(abs_el))]
    abstract = "\n".join(abstract_parts) if abstract_parts else ""

    # Body
    blocks: list[ParsedBlock] = []
    body = article.find(".//{*}body") or article.find(".//body")
    if body is not None:
        for sec in body:
            if _local_tag(sec) == "sec":
                _parse_sec(sec, [], blocks)
            elif _local_tag(sec) == "p":
                text = _normalize_whitespace(_text_content(sec))
                if text:
                    blocks.append(
                        ParsedBlock(
                            block_type="paragraph",
                            text=text,
                            section_path=[],
                            page=1,
                        )
                    )

    # Metadata
    metadata: dict[str, Any] = {}
    pmid_el = article.find(".//{*}article-id[@pub-id-type='pmid']") or article.find(".//article-id[@pub-id-type='pmid']")
    if pmid_el is not None:
        metadata["pmid"] = _text_content(pmid_el)
    pmc_el = article.find(".//{*}article-id[@pub-id-type='pmc']") or article.find(".//article-id[@pub-id-type='pmc']")
    if pmc_el is not None:
        metadata["pmc_id"] = _text_content(pmc_el)

    return ParsedDocument(title=title, abstract=abstract, blocks=blocks, metadata=metadata)


def parse_raw_text(path: str | Path) -> ParsedDocument | None:
    """
    Fallback: parse raw text file (e.g., from PDF extraction).
    Treats each non-empty paragraph as a block with no section structure.
    """
    path = Path(path)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    blocks: list[ParsedBlock] = []
    current: list[str] = []
    for line in lines:
        line = line.strip()
        if line:
            current.append(line)
        elif current:
            blocks.append(
                ParsedBlock(
                    block_type="paragraph",
                    text=" ".join(current),
                    section_path=[],
                    page=1,
                )
            )
            current = []
    if current:
        blocks.append(
            ParsedBlock(
                block_type="paragraph",
                text=" ".join(current),
                section_path=[],
                page=1,
            )
        )
    title = blocks[0].text[:200] + "..." if blocks and len(blocks[0].text) > 200 else (blocks[0].text if blocks else "")
    return ParsedDocument(title=title, abstract="", blocks=blocks, metadata={})
