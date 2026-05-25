from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
import re

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def clean_filing_text(raw_html: str) -> str:
    """
    Clean an iXBRL/HTML SEC filing down to readable prose only.
    Strips XBRL inline tags, boilerplate, and noise.
    """
    soup = BeautifulSoup(raw_html, "lxml")

    # Remove non-content tags entirely
    for tag in soup(["script", "style", "header", "footer", "nav",
                     "ix:header", "ix:hidden", "ix:resources"]):
        tag.decompose()

    # Unwrap iXBRL inline tags but keep their text content
    # e.g. <ix:nonfraction ...>1,234</ix:nonfraction> → "1,234"
    for tag in soup.find_all(re.compile(r"^ix:")):
        tag.unwrap()

    # Remove XBRL namespace noise lines (us-gaap:..., dei:..., etc.)
    text = soup.get_text(separator="\n")

    lines = []
    for line in text.splitlines():
        stripped = line.strip()

        # Skip XBRL taxonomy lines
        if re.match(r"^(us-gaap|dei|ifrs|srt|invest|country|currency):", stripped):
            continue
        # Skip lines that are pure XML/namespace identifiers
        if re.match(r"^[a-zA-Z]+:[A-Z][a-zA-Z]+$", stripped):
            continue
        # Skip lines that look like EDGAR/XBRL context IDs
        if re.match(r"^c-\d+$", stripped) or re.match(r"^D\d{8}", stripped):
            continue
        # Skip very short lines (page numbers, stray characters)
        if len(stripped) <= 2:
            continue

        lines.append(stripped)

    text = "\n".join(lines)

    # Collapse runs of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()