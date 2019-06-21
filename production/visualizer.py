import os
import sys
import contextlib
from enum import IntEnum
from collections import defaultdict

import curses

from production import geom, utils
from production.data_formats import Task, Action, Pt



class Game:
    def __init__(self, task: Task):
        self.task = task
        self.grid = geom.rasterize_to_grid(task)
        self.height = len(self.grid)
        self.width = len(self.grid[0])
        self.pos = task.start
        self.boosters = task.boosters
        self.wrapped = set()
        self.update_wrapped()


    def update_wrapped(self):
        self.wrapped.add(self.pos)


    def is_wrapped(self, y, x):
        return Pt(x, y) in self.wrapped


    def apply_action(self, action: Action):
        '' #if action.s in


class FgColors(IntEnum):
    Player = curses.COLOR_RED
    Booster = curses.COLOR_GREEN
    Dungeon = curses.COLOR_WHITE


def bg_color(ch):
    return


class Colormapping(defaultdict):
    counter = iter(range(1, 1000))
    def __missing__(self, key):
        idx = next(self.counter)
        fg, bg = key
        curses.init_pair(idx, fg, bg)
        res = curses.color_pair(idx)
        self[key] = res
        return res

colormapping = Colormapping()


class Display:
    def __init__(self, game):
        self.width, self.height = game.width, game.height
        self.stdscr = curses.initscr()
        self.pad = curses.newpad(self.height, self.width * 2)

        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        self.stdscr.refresh() # needed for some reason

        curses.start_color()


    # pass game here in case at some point it becomes purely functional
    def draw(self, game: Game):
        stdscr, pad = self.stdscr, self.pad

        def char(y, x, char, fgcolor):
            bg_color = curses.COLOR_YELLOW if game.is_wrapped(y, x) else curses.COLOR_BLACK
            pad.addch(self.height - y - 1, x * 2, char, colormapping[fgcolor, bg_color])

        for y, row in enumerate(game.grid):
            for x, c in enumerate(row):
                char(y, x, c, FgColors.Dungeon)
        char(game.pos.y, game.pos.x, '@', FgColors.Player)
        for b in game.boosters:
            char(b.pos.y, b.pos.x, b.code, FgColors.Booster)
        pad.refresh(0, 0, 0, 0, curses.LINES - 2, curses.COLS - 1)
        stdscr.refresh()


    def close(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


def interactive():
    task = Task.parse(utils.get_problem_raw(3))
    game = Game(task)

    with contextlib.closing(Display(game)) as display:
        while True:
            display.draw(game)

            c = display.stdscr.getch()
            action = None

            if c in (27, ord('q')):
                break
            elif c in WSAD:
                action = Action.WSAD(c)

            if action:
                game.apply_action(action)






if __name__ == '__main__':
    interactive()
