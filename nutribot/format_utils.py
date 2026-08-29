import re
from typing import List


def normalize_markdown_tables(text: str) -> str:
    """
    Heuristically normalize markdown tables so they render in Streamlit:
    - Ensure there's a blank line before a table header line containing '|'
    - If consecutive lines contain '|' but there's no separator line, insert a separator
      line of '---' per column to form a proper markdown table.
    """
    if not text:
        return text

    lines = text.splitlines()
    out_lines: List[str] = []
    i = 0
    sep_re = re.compile(r"^\s*\|?\s*[:\-]+(?:\s*\|\s*[:\-]+)*\s*\|?\s*$")
    while i < len(lines):
        line = lines[i]
        # detect potential table header
        if '|' in line:
            # look ahead to next line
            next_i = i + 1
            if next_i < len(lines) and '|' in lines[next_i] and not sep_re.match(lines[next_i]):
                # ensure blank line before header
                if out_lines and out_lines[-1].strip() != '':
                    out_lines.append('')

                out_lines.append(line)
                # create separator matching number of columns
                cols = [c for c in re.split(r"\|", line) if c.strip() != '']
                if not cols:
                    # fallback: simple separator
                    sep = '| ' + ' | '.join(['---']) + ' |'
                else:
                    sep = '| ' + ' | '.join(['---'] * len(cols)) + ' |'
                out_lines.append(sep)
                i += 1
                # after inserting separator, skip to next line but include the next (content) line
                # include the next line as content
                out_lines.append(lines[i])
                i += 1
                continue

        out_lines.append(line)
        i += 1

    return '\n'.join(out_lines)
