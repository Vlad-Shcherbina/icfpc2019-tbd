import os
import sys
import contextlib
from enum import IntEnum
from collections import defaultdict

import curses

from production import geom, utils
from production.data_formats import GridTask, Action, Pt
from production.game import Game, InvalidActionException

'''
Interactive task runner / replay visualizer.

Arguments:
0 - interactive on task 1
1 - interactive on a given task
2 - visualize a given task and trace

Interactive controls:
ESC - quit
WASD - movement
QE - turning
'''

class Colormapping(defaultdict):
    counter = iter(range(1, 1000))
    def __missing__(self, key):
        idx = next(self.counter)
        fg, bg = key
        attr = 0
        if fg & BRIGHT:
            fg ^= BRIGHT
            attr = curses.A_BOLD

        curses.init_pair(idx, fg, bg)
        res = curses.color_pair(idx) | attr
        self[key] = res
        return res

colormapping = Colormapping()


# can be added to foreground color to hackishly make it bright (or bold on some terminals)
BRIGHT = 0x10000

class FgColors(IntEnum):
    Player = curses.COLOR_RED | BRIGHT
    Booster = curses.COLOR_GREEN | BRIGHT
    Manipulator = curses.COLOR_CYAN | BRIGHT
    Dungeon = curses.COLOR_WHITE


class Display:
    def __init__(self, game):
        self.width, self.height = game.width, game.height
        self.stdscr = curses.initscr()
        self.pad = curses.newpad(self.height, self.width * 2 + 1) # same shit about the last character

        self.last_error = ''

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.stdscr.leaveok(1)
        self.stdscr.keypad(1)
        self.stdscr.refresh() # needed for some reason

        curses.start_color()


    # pass game here in case at some point it becomes purely functional
    def draw(self, game: Game, extra_status = ''):
        stdscr, pad = self.stdscr, self.pad

        def char(p, char, fgcolor):
            bg_color = curses.COLOR_BLUE if game.is_wrapped(p) else curses.COLOR_BLACK
            pad.addstr(self.height - p.y - 1, p.x * 2, char + ' ', colormapping[fgcolor, bg_color])

        for y, row in enumerate(game.grid):
            for x, c in enumerate(row):
                char(Pt(x, y), c, FgColors.Dungeon)

        for m in game.world_manipulator:
            char(m, '*', FgColors.Manipulator)

        for b in game.boosters:
            char(b.pos, b.code, FgColors.Booster)

        char(game.pos, '@', FgColors.Player)

        pad.refresh(0, 0, 0, 0, curses.LINES - 2, curses.COLS - 1)

        if self.last_error:
            status_line = self.last_error.ljust(curses.COLS)[:curses.COLS - 1]
            self.last_error = ''
            stdscr.addstr(curses.LINES - 1, 0, status_line, colormapping[curses.COLOR_YELLOW | BRIGHT, curses.COLOR_RED])
        else:
            status_line = f'{game.world_manipulator} '
            status_line += extra_status
            # LMAO: "It looks like simply writing the last character of a window is impossible with curses, for historical reasons."
            status_line = status_line.ljust(curses.COLS)[:curses.COLS - 1]
            stdscr.addstr(curses.LINES - 1, 0, status_line, colormapping[curses.COLOR_YELLOW | BRIGHT, curses.COLOR_BLUE])

        stdscr.refresh()


    def draw_error(self, err):
        self.last_error = err


    def close(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


def interactive(task_number):
    task = GridTask.from_problem(task_number, with_border=True)
    game = Game(task)
    score = None

    with contextlib.closing(Display(game)) as display:
        code, c = '', ''
        while not score:
            display.draw(game, f'lastchar = {code} {c!r}')

            code = display.stdscr.getch()
            action = None

            c = chr(code).upper()

            if c in '\x1B':
                break

            action = Action.from_key(c)

            if action:
                try:
                    game.apply_action(action)
                except InvalidActionException as exc:
                    display.draw_error(str(exc))

            score = game.finished()

    if score:
        print(f'Score: {score}')
        # TODO: submit solution


def main(args=None):
    args = sys.argv[1:] if args is None else args
    if len(args) == 0:
        interactive(1)
    elif len(args) == 1:
        interactive(int(args))
    elif len(args) == 2:
        raise NotImplementedError()
    else:
        assert False


if __name__ == '__main__':
    main()
