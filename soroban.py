#!/usr/bin/env python3
# animated_soroban_rich_beadwise.py
"""
Bead-by-bead Soroban animation with Rich.

to run, you need to:

    pip install rich

• Each bead moves individually (0.5 s between moves).
• After finishing a column, the animation pauses 0.5 s.
• If that column created a carry, a second 0.5 s pause is added.
• Uses Rich.Live to keep one abacus “in place” on the screen.
"""

import sys, time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

BEAD = "⬬"     # active bead (single-width, looks good in most fonts)
ROD  = "|"      # gap symbol, ASCII single-width
PER_BEAD_PAUSE = 0.5  # seconds to pause between moving individual beads
PER_COLUMN_PAUSE = 0.5 # Seconds to pause between columns
PER_CARRY_PAUSE = 0.75
# ────────────────────────────────────────────────────────────────
#  Render Soroban for an integer given as zero-padded string
# ────────────────────────────────────────────────────────────────
def draw_soroban(num_str: str) -> str:
    n = len(num_str)
    top_up, top_down = [], []
    lower = [[] for _ in range(5)]  # rows 0-4, row 0 nearest divider

    for ch in num_str:
        d = int(ch)

        # upper bead (value 5)
        if d >= 5:                  # bead is down → active
            top_up.append(ROD)
            top_down.append(BEAD)
        else:                       # bead is up   → inactive
            top_up.append(BEAD)
            top_down.append(ROD)

        # lower beads (value 1 × 4)
        k = d % 5                   # beads “up” (near divider)
        for i in range(5):
            if i < k:               lower[i].append(BEAD)       # active
            elif i == k:            lower[i].append(ROD)        # gap
            else:                   lower[i].append(BEAD)       # inactive

    def fmt(row): return f"‖{' '.join(row)}‖"
    inside = 2 * n - 1              # length of the "x x x" interior
    frame  = f"‖{'=' * inside}‖"

    return "\n".join(
        [frame, fmt(top_up), fmt(top_down), frame]
        + [fmt(r) for r in lower]
        + [frame]
    )


# ────────────────────────────────────────────────────────────────
#  Bead-wise column addition with animation
# ────────────────────────────────────────────────────────────────
def animate_add(a: int, b: int) -> None:
    total = a + b
    width = len(str(total))                     # columns needed

    # working digits (mutable), zero-padded to the width of result
    digits = list(map(int, str(a).zfill(width)))
    addend = list(map(int, str(b).zfill(width)))

    console = Console()

    def panel() -> Panel:
        return Panel(
            draw_soroban("".join(map(str, digits))),
            title=f"[bold]{a} + {b} = {total}[/bold]",
            border_style="cyan",
        )

    with Live(panel(), console=console, refresh_per_second=30, screen=True) as live:
        carry = 0
        # walk columns right-to-left
        for pos in range(width - 1, -1, -1):
            increments = addend[pos] + carry
            carry = 0                        # reset; will be set again if overflow

            # move beads one-by-one
            for _ in range(increments):
                digits[pos] += 1
                if digits[pos] == 10:        # overflow → carry out
                    digits[pos] = 0
                    carry = 1
                live.update(panel())
                time.sleep(PER_BEAD_PAUSE)              # pause between individual bead moves

            # finished this column
            time.sleep(PER_COLUMN_PAUSE)
            if carry:                        # extra pause if carry created
                time.sleep(PER_CARRY_PAUSE)

        # final display stays for a moment
        live.update(panel())
        time.sleep(1)


# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        x = int(input("Enter first  number: "))
        y = int(input("Enter second number: "))
    except ValueError:
        print("Integers only."); sys.exit(1)

    animate_add(x, y)
