"""Two MCP servers that do the same job with different reach. Demo 13 connects to both.

    uv run python demos/13_two_servers.py wide     # read_url(url): any string at all
    uv run python demos/13_two_servers.py narrow   # read_page(page): one of three names

Neither touches the network. The wide one only says what it WOULD fetch, which is the
point: its schema lets through anything a caller types, and the checking is left to code
somebody has to remember to write.
"""

import sys
from typing import Literal

from mcp.server import MCPServer

PAGES = {
    "pricing": "Espresso 0.10 USDC. Beans 0.40 USDC a bag.",
    "opening-hours": "Monday to Friday, 8:00 to 18:00.",
    "refunds": "Refunds within 24 hours, to the wallet that paid.",
}

wide = MCPServer("shop-pages-wide")
narrow = MCPServer("shop-pages-narrow")


@wide.tool(annotations={"readOnlyHint": True})
def read_url(url: str) -> str:
    """Read a page of the shop's website."""
    return f"would fetch {url!r} (this demo never opens a socket)"


@narrow.tool(annotations={"readOnlyHint": True})
def read_page(page: Literal["pricing", "opening-hours", "refunds"]) -> str:
    """Read one page of the shop's website, by name."""
    return PAGES[page]


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "narrow"
    {"wide": wide, "narrow": narrow}[which].run()
