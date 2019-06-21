import os
import sys
import contextlib
from enum import IntEnum
from collections import defaultdict

import curses

from production import geom, utils
from production.data_formats import GridTask, Action, Pt


class InvalidActionException(Exception):
    pass


class Game:
    def __init__(self, task: GridTask):
        self.task = task
        self.grid = task.grid
        self.height = task.height
        self.width = task.width
        self.pos = task.start
        self.boosters = task.boosters
        self.wrapped = set()
        self.update_wrapped()


    def update_wrapped(self):
        self.wrapped.add(self.pos)


    def is_wrapped(self, y, x):
        return Pt(x, y) in self.wrapped


    def apply_action(self, action: Action):
        if action.s in 'WSAD':
            np = self.pos + action.WSAD2DIR[action.s]
            if self.grid[np.y][np.x] != '.':
                raise InvalidActionException(f'Can\'t move into a tile: {self.grid[np.y][np.x]!r}')
            self.pos = np
            self.update_wrapped()
        else:
            raise InvalidActionException(f'Unknown action {action}')


# can be added to foreground color to hackishly make it bright (or bold on some terminals)
BRIGHT = 0x10000


class FgColors(IntEnum):
    Player = curses.COLOR_RED | BRIGHT
    Booster = curses.COLOR_GREEN | BRIGHT
    Dungeon = curses.COLOR_WHITE


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

        def char(y, x, char, fgcolor):
            bg_color = curses.COLOR_BLUE if game.is_wrapped(y, x) else curses.COLOR_BLACK
            pad.addstr(self.height - y - 1, x * 2, char + ' ', colormapping[fgcolor, bg_color])

        for y, row in enumerate(game.grid):
            for x, c in enumerate(row):
                char(y, x, c, FgColors.Dungeon)

        for b in game.boosters:
            char(b.pos.y, b.pos.x, b.code, FgColors.Booster)

        char(game.pos.y, game.pos.x, '@', FgColors.Player)

        pad.refresh(0, 0, 0, 0, curses.LINES - 2, curses.COLS - 1)

        if self.last_error:
            status_line = self.last_error.ljust(curses.COLS)[:curses.COLS - 1]
            self.last_error = ''
            stdscr.addstr(curses.LINES - 1, 0, status_line, colormapping[curses.COLOR_YELLOW | BRIGHT, curses.COLOR_RED])
        else:
            status_line = ''
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


def interactive():
    task = GridTask.from_problem(3, with_border=True)
    game = Game(task)

    with contextlib.closing(Display(game)) as display:
        code, c = '', ''
        while True:
            display.draw(game, f'lastchar = {code} {c!r}')

            code = display.stdscr.getch()
            action = None

            c = chr(code).upper()

            if c in '\x1BQ':
                break
            elif c in 'WSAD':
                action = Action.WSAD(c)

            if action:
                try:
                    game.apply_action(action)
                except InvalidActionException as exc:
                    display.draw_error(str(exc))






if __name__ == '__main__':
    interactive()
