"""Decode the secret message hidden in a published Google Doc.

The doc contains a table where each data row has a Unicode character and its
(x, y) coordinates in a 2D grid. This module fetches the doc, parses the
table, and prints the grid so the characters reveal a message.
"""

from html.parser import HTMLParser
from urllib.request import urlopen


class _DocTableParser(HTMLParser):
    """Collect the text content of every <td> cell in document order."""

    def __init__(self):
        super().__init__()
        self._in_td = 0
        self._buffer = []
        self.cells = []

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self._in_td += 1
            self._buffer = []

    def handle_endtag(self, tag):
        if tag == "td" and self._in_td:
            self._in_td -= 1
            self.cells.append("".join(self._buffer))
            self._buffer = []

    def handle_data(self, data):
        if self._in_td:
            self._buffer.append(data)

    def handle_entityref(self, name):
        if self._in_td:
            self._buffer.append(f"&{name};")

    def handle_charref(self, name):
        if self._in_td:
            self._buffer.append(f"&#{name};")


def _extract_rows(html):
    parser = _DocTableParser()
    parser.feed(html)
    cells = [c.strip() for c in parser.cells]

    # The table has three columns: x-coordinate, Character, y-coordinate.
    # The first three cells are the header; the rest are data rows.
    if len(cells) < 6 or len(cells) % 3 != 0:
        raise ValueError("Unexpected table shape in Google Doc")

    header = [h.lower() for h in cells[:3]]
    x_idx = next(i for i, h in enumerate(header) if "x" in h)
    y_idx = next(i for i, h in enumerate(header) if "y" in h)
    char_idx = next(i for i in range(3) if i not in (x_idx, y_idx))

    rows = []
    for i in range(3, len(cells), 3):
        triple = cells[i:i + 3]
        rows.append((int(triple[x_idx]), triple[char_idx], int(triple[y_idx])))
    return rows


def print_grid(url):
    """Fetch the published Google Doc at `url` and print its grid."""
    with urlopen(url) as response:
        html = response.read().decode("utf-8")

    points = _extract_rows(html)
    if not points:
        return

    width = max(x for x, _, _ in points) + 1
    height = max(y for _, _, y in points) + 1

    grid = [[" "] * width for _ in range(height)]
    for x, ch, y in points:
        grid[y][x] = ch

    # y = 0 is the bottom row, so print from the highest y downward.
    for row in reversed(grid):
        print("".join(row).rstrip())


if __name__ == "__main__":
    import sys
    print_grid(sys.argv[1])
