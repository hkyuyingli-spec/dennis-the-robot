import re
from typing import List

TABLE_SEP_REGEX = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")


def is_dash_row(line: str) -> bool:
    """
    Returns True if a row consists only of dashes, dots, colons, pipes, or whitespace
    and lacks any alphanumeric / ideographic characters.
    """
    stripped = line.strip()
    if not stripped:
        return False
    return not bool(re.search(r"[\w\u4e00-\u9fff]", stripped))


def is_table_separator(line: str) -> bool:
    """Returns True if the line is a valid markdown table separator row."""
    return bool(TABLE_SEP_REGEX.match(line.strip()))


def has_broken_table_header(text: str) -> bool:
    """
    Defense-in-depth check: detects if any markdown table has a header row
    consisting only of dashes, dots, or whitespace (e.g. '| ---------- | ---------- |'
    immediately followed by a markdown separator row '|---|---|').
    """
    if not text:
        return False
    lines = text.splitlines()
    for i in range(len(lines) - 1):
        line = lines[i].strip()
        next_line = lines[i + 1].strip()
        if "|" in line and is_table_separator(next_line):
            if is_dash_row(line):
                return True
    return False


def has_incomplete_table(text: str) -> bool:
    """
    Detect a table that starts but is cut off before completion.

    Typical examples include a starter header like '| Food' or a pipe-delimited line
    without a valid separator row and without enough completed rows to constitute a
    finished markdown table. This is a direct defense against model truncation when
    the completion was cut off by max_tokens.
    """
    if not text or "|" not in text:
        return False

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    pipe_lines = [line for line in lines if "|" in line]
    if not pipe_lines:
        return False

    # A valid markdown table needs a separator row. If there is no separator row at all
    # and we see pipe-delimited content, the model likely stopped mid-generation.
    if not any(is_table_separator(line) for line in lines):
        if len(pipe_lines) >= 2:
            return True
        if pipe_lines[0].startswith("|"):
            return True

    # Detect a partial header followed by no completed body.
    for i, line in enumerate(lines[:-1]):
        if "|" in line and not is_table_separator(line):
            next_line = lines[i + 1]
            if "|" in next_line and not is_table_separator(next_line):
                # Header-or-row started, but the model never got far enough to finish a real table.
                return True

    return False


def normalize_markdown_tables(text: str) -> str:
    """
    Heuristically normalize markdown tables so they render properly in Streamlit:
    - Ensure there's a blank line before a table header line containing '|'
    - Fix malformed headers: if a header row consists only of dashes/dots/whitespace,
      resolve or clean it so a string of dashes is not displayed as the header.
    - If a table header has no separator line, insert a separator line of '---' per column.
    - Do not inject separators into the table body between data rows.
    """
    if not text:
        return text

    lines = text.splitlines()
    out_lines: List[str] = []
    i = 0
    in_table = False

    while i < len(lines):
        line = lines[i]
        has_pipe = "|" in line

        if has_pipe:
            if not in_table:
                # We are at the start of a table
                in_table = True

                # Check for decorative top border (e.g. | ---- | followed by | Season | Focus |)
                if (
                    is_dash_row(line)
                    and (i + 1 < len(lines))
                    and ("|" in lines[i + 1])
                    and not is_dash_row(lines[i + 1])
                ):
                    if (i + 2 < len(lines)) and is_table_separator(lines[i + 2]):
                        i += 1
                        line = lines[i]

                # Check if header is broken (all dashes) followed by separator
                if (
                    is_dash_row(line)
                    and (i + 1 < len(lines))
                    and is_table_separator(lines[i + 1])
                ):
                    after_sep = i + 2
                    if (
                        after_sep + 1 < len(lines)
                        and "|" in lines[after_sep]
                        and is_table_separator(lines[after_sep + 1])
                        and not is_dash_row(lines[after_sep])
                    ):
                        # Phantom duplicate dash header + separator
                        i = after_sep
                        line = lines[i]
                    else:
                        cols = [c.strip() for c in line.split("|") if c.strip() != ""]
                        col_count = len(cols) if cols else 2
                        if col_count == 2:
                            col_names = ["Category", "Details"]
                        elif col_count == 3:
                            col_names = ["Category", "Focus", "Recommendation"]
                        elif col_count == 4:
                            col_names = ["Season", "Focus", "Diet", "Practice"]
                        else:
                            col_names = [f"Item {idx + 1}" for idx in range(col_count)]
                        line = "| " + " | ".join(col_names) + " |"

                # Ensure blank line before table
                if out_lines and out_lines[-1].strip() != "":
                    out_lines.append("")

                out_lines.append(line)

                # Check if next line is already a separator
                if i + 1 < len(lines) and is_table_separator(lines[i + 1]):
                    i += 1
                    out_lines.append(lines[i])
                else:
                    # Missing separator: generate one
                    cols = [c for c in re.split(r"\|", line) if c.strip() != ""]
                    sep = "| " + " | ".join(["---"] * (len(cols) if cols else 1)) + " |"
                    out_lines.append(sep)

                i += 1
                continue
            else:
                # Inside table body: keep rows as-is
                out_lines.append(line)
                i += 1
                continue
        else:
            in_table = False
            out_lines.append(line)
            i += 1

    return "\n".join(out_lines)
