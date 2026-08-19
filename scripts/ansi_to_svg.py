#!/usr/bin/env python3
"""Convert the ANSI terminal stream used by the profile card to standalone SVG.

Fastfetch positions its right-hand column with cursor movement sequences, so this
implements the small terminal-emulation subset needed by Fastfetch and jp2a.
"""

from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path


CSI_RE = re.compile(r"\x1b\[([0-9;?]*)([@-~])")

NORMAL = [
    "#45475a", "#f38ba8", "#a6e3a1", "#f9e2af",
    "#89b4fa", "#cba6f7", "#94e2d5", "#cdd6f4",
]
BRIGHT = [
    "#585b70", "#f37799", "#89d88b", "#ebd391",
    "#74a8fc", "#b995e8", "#6bd7ca", "#ffffff",
]


@dataclass
class Style:
    color: str = "#cdd6f4"
    bold: bool = False


def indexed_color(index: int) -> str:
    if index < 8:
        return NORMAL[index]
    if index < 16:
        return BRIGHT[index - 8]
    if index < 232:
        index -= 16
        red, remainder = divmod(index, 36)
        green, blue = divmod(remainder, 6)

        def component(value: int) -> int:
            return 0 if value == 0 else 55 + value * 40

        return f"#{component(red):02x}{component(green):02x}{component(blue):02x}"
    gray = 8 + (index - 232) * 10
    return f"#{gray:02x}{gray:02x}{gray:02x}"


def apply_codes(style: Style, codes: list[int]) -> Style:
    updated = Style(style.color, style.bold)
    index = 0
    while index < len(codes):
        code = codes[index]
        if code == 0:
            updated = Style()
        elif code == 1:
            updated.bold = True
        elif code == 22:
            updated.bold = False
        elif 30 <= code <= 37:
            updated.color = NORMAL[code - 30]
        elif 90 <= code <= 97:
            updated.color = BRIGHT[code - 90]
        elif code == 39:
            updated.color = Style().color
        elif code == 38 and index + 2 < len(codes) and codes[index + 1] == 5:
            updated.color = indexed_color(codes[index + 2])
            index += 2
        elif code == 38 and index + 4 < len(codes) and codes[index + 1] == 2:
            red, green, blue = codes[index + 2:index + 5]
            updated.color = f"#{red:02x}{green:02x}{blue:02x}"
            index += 4
        index += 1
    return updated


def parameters(raw: str, default: int = 1) -> list[int]:
    raw = raw.lstrip("?")
    if not raw:
        return [default]
    return [int(value) if value else default for value in raw.split(";")]


def emulate(ansi: str) -> dict[int, dict[int, tuple[str, Style]]]:
    screen: dict[int, dict[int, tuple[str, Style]]] = {}
    row = 0
    column = 0
    saved_position = (0, 0)
    style = Style()
    index = 0

    def put(character: str) -> None:
        nonlocal column
        screen.setdefault(row, {})[column] = (
            character,
            Style(style.color, style.bold),
        )
        column += 1

    while index < len(ansi):
        character = ansi[index]

        if character == "\x1b":
            if index + 1 < len(ansi) and ansi[index + 1] == "]":
                bell = ansi.find("\x07", index + 2)
                terminator = ansi.find("\x1b\\", index + 2)
                candidates = [position for position in (bell, terminator) if position >= 0]
                if not candidates:
                    break
                end = min(candidates)
                index = end + (2 if ansi[end:end + 2] == "\x1b\\" else 1)
                continue

            match = CSI_RE.match(ansi, index)
            if match:
                raw, command = match.groups()
                values = parameters(raw)
                amount = values[0]

                if command == "m":
                    sgr_values = [int(value or 0) for value in raw.split(";")] if raw else [0]
                    style = apply_codes(style, sgr_values)
                elif command == "A":
                    row = max(0, row - amount)
                elif command == "B":
                    row += amount
                elif command == "C":
                    column += amount
                elif command == "D":
                    column = max(0, column - amount)
                elif command == "E":
                    row += amount
                    column = 0
                elif command == "F":
                    row = max(0, row - amount)
                    column = 0
                elif command == "G":
                    column = max(0, amount - 1)
                elif command in ("H", "f"):
                    target = parameters(raw)
                    row = max(0, target[0] - 1)
                    column = max(0, (target[1] if len(target) > 1 else 1) - 1)
                elif command == "K":
                    current = screen.setdefault(row, {})
                    if amount == 1:
                        for target in [key for key in current if key <= column]:
                            current.pop(target, None)
                    elif amount == 2:
                        current.clear()
                    else:
                        for target in [key for key in current if key >= column]:
                            current.pop(target, None)
                elif command == "s":
                    saved_position = (row, column)
                elif command == "u":
                    row, column = saved_position

                index = match.end()
                continue

            # Skip a two-byte escape sequence we do not need to emulate.
            index += 2
            continue

        if character == "\n":
            row += 1
            column = 0
        elif character == "\r":
            column = 0
        elif character == "\t":
            spaces = 4 - (column % 4)
            for _ in range(spaces):
                put(" ")
        elif character >= " ":
            put(character)

        index += 1

    return screen


def row_spans(cells: dict[int, tuple[str, Style]]) -> tuple[list[tuple[str, Style]], int]:
    if not cells:
        return [], 0

    width = max(cells) + 1
    spans: list[tuple[str, Style]] = []
    current_style = Style()
    current_text = ""

    for column in range(width):
        character, cell_style = cells.get(column, (" ", Style()))
        if cell_style != current_style and current_text:
            spans.append((current_text, current_style))
            current_text = ""
        current_style = cell_style
        current_text += character

    if current_text:
        spans.append((current_text, current_style))
    return spans, width


def main() -> None:
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "github-terminal.svg")
    screen = emulate(sys.stdin.read())
    last_row = max((row for row, cells in screen.items() if cells), default=0)
    parsed = [row_spans(screen.get(row, {})) for row in range(last_row + 1)]
    columns = max((width for _, width in parsed), default=1)

    font_size = 15
    character_width = 9.05
    line_height = 21
    padding_x = 24
    padding_y = 26
    width = round(columns * character_width + padding_x * 2)
    height = max(1, len(parsed)) * line_height + padding_y * 2

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="GitHub profile terminal metrics" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '  <rect width="100%" height="100%" rx="14" fill="#1e1e2e"/>',
        '  <g font-family="SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace" '
        f'font-size="{font_size}" xml:space="preserve">',
    ]

    for line_number, (spans, _) in enumerate(parsed):
        y = padding_y + font_size + line_number * line_height
        span_markup: list[str] = []
        for text, style in spans:
            weight = ' font-weight="700"' if style.bold else ""
            span_markup.append(
                f'<tspan fill="{style.color}"{weight}>{html.escape(text)}</tspan>'
            )
        # Keep tspans adjacent. With xml:space="preserve", source-code newlines and
        # indentation between tspans would become visible terminal spaces.
        lines.append(
            f'    <text x="{padding_x}" y="{y}">{"".join(span_markup)}</text>'
        )

    lines.extend(["  </g>", "</svg>"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"rendered {output} ({width}x{height}, {len(parsed)} lines)", file=sys.stderr)


if __name__ == "__main__":
    main()
