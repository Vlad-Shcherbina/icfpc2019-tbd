import os
import sys
import contextlib
from enum import IntEnum
from collections import defaultdict
import zlib
import getpass

import curses

from production import geom, utils
from production.data_formats import Task, GridTask, Action, Pt, Booster, compose_actions
from production.game import Game, InvalidActionException
from production import db
from production import solver_worker
from production.solvers import interface
from production.golden import validate

'''
Interactive task runner / replay visualizer.

Arguments:
0 - interactive on task 1
1 - interactive on a given task
2 - --no-db prevents from writing to db (for mock tasks)

Interactive controls:
ESC - quit
WASD - movement
QE - turning
Z - waiting
FLBTRC - boosters
Space or Anykey - dismiss error message
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
    InactivePlayer = curses.COLOR_RED
    Booster = curses.COLOR_GREEN | BRIGHT
    Manipulator = curses.COLOR_CYAN | BRIGHT
    Dungeon = curses.COLOR_WHITE
    Spot = curses.COLOR_YELLOW | BRIGHT


class Display:
    def __init__(self, game):
        self.width, self.height = game.width, game.height
        self.stdscr = curses.initscr()
        self.pad = curses.newpad(self.height + 3, self.width * 2 + 3) # same shit about the last character

        self.last_error = ''
        self.current = 0

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
            offset = Pt(1, 1)
            bg_color = curses.COLOR_BLUE if game.is_wrapped(p) else curses.COLOR_BLACK
            p = p + offset
            pad.addstr(self.height - p.y + 1, p.x * 2, char + ' ', colormapping[fgcolor, bg_color])

        #borders
        #for some reason the left border is not shown
        for x in range(game.width + 2):
            char(Pt(x - 1, -1), 'H', FgColors.Dungeon)
            char(Pt(x - 1, game.height), 'H', FgColors.Dungeon)
        for y in range(game.height + 2):
            char(Pt(-1, y - 1), 'H', FgColors.Dungeon)
            char(Pt(game.width, y - 1), 'H', FgColors.Dungeon)
            
        for y, row in enumerate(game.grid):
            for x, c in enumerate(row):
                char(Pt(x, y), c, FgColors.Dungeon)

        for b in game.boosters:
            char(b.pos, b.code, FgColors.Booster)

        for t in game.teleport_spots:
            char(t, '+', FgColors.Spot)

        for c in game.clone_spawn:
            char(c, 'X', FgColors.Spot)

        for bot in game.bots:
            for m in bot.world_manipulator:
                char(m, '*', FgColors.Manipulator)

        for bot in game.bots:
            char(bot.pos, '@', FgColors.InactivePlayer)

        char(game.bots[self.current].pos, '@', FgColors.Player)



        pad.refresh(0, 0, 0, 0, curses.LINES - 2, curses.COLS - 1)

        if self.last_error:
            status_line = self.last_error.ljust(curses.COLS)[:curses.COLS - 1]
            self.last_error = ''
            stdscr.addstr(curses.LINES - 1, 0, status_line, colormapping[curses.COLOR_YELLOW | BRIGHT, curses.COLOR_RED])
        else:
            status_line = f'turn={game.turn} ' + \
                          f'pos=({game.bots[self.current].pos.x}, {game.bots[self.current].pos.y}) ' + \
                          f'unwrapped={len(game.unwrapped)} '
            status_line += ' '.join(f'{b}={game.inventory[b]}' for b in Booster.PICKABLE)

            if game.bots[self.current].wheels_timer:
                status_line += f' WHEELS({game.bots[self.current].wheels_timer})'

            if game.bots[self.current].drill_timer:
                status_line += f' DRILL({game.bots[self.current].drill_timer})'

            if extra_status:
                status_line += ' '
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


def interactive(task_number, use_db=True):
    task_data = utils.get_problem_raw(task_number)

    if use_db:
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute('''
        SELECT id, data FROM tasks WHERE name = %s
        ''',
        [f'prob-{task_number:03d}'])
        [task_id, task_data_db] = cur.fetchone()
        task_data_db = zlib.decompress(task_data_db).decode()
        assert task_data_db == task_data

    task = GridTask(Task.parse(task_data))
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

            if c in Action.SIMPLE:
                action = Action.simple_action(c)

            # to perform complex action type it without spaces: B(1,-1)
            elif c in Action.PARAM:
                while c[-1] != ')':
                    code = display.stdscr.getch()
                    c = c + chr(code).upper()
                action = Action.parameterized_action(c)

            if action:
                try:
                    end_turn = display.current == len(game.bots) - 1
                    game.apply_action(action, display.current, end_turn)
                except InvalidActionException as exc:
                    display.draw_error(str(exc))
                else:
                    display.current = (display.current + 1) % len(game.bots)

            score = game.finished()


    if score is not None:
        print(f'Score: {score}')
        result = validate_replay(task_data, score, game.get_actions())
        if use_db:
            submit_replay(conn, task_id, result)


def validate_replay(task_data, expected_score, actions):
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    solution_data = compose_actions(actions)
    sr = interface.SolverResult(
        data=solution_data,
        expected_score=expected_score)

    scent = f'manual ({getpass.getuser()})'

    logging.info('Checking with validator...')
    er = validate.run(task_data, sr.data)
    if er.time is None:
        result = solver_worker.Result(
            status='CHECK_FAIL', scent=scent, score=None,
            solution=solution_data,
            extra=dict(
                validator=er.extra,
                expected_score=sr.expected_score))
        logging.info(result)
    else:
        result = solver_worker.Result(
            status='DONE', scent=scent, score=er.time,
            solution=solution_data,
            extra=dict(
                validator=er.extra,
                expected_score=sr.expected_score))
        logging.info(f'Validator score: {er.time}')
    return result


def submit_replay(conn, task_id, result):
    solver_worker.put_solution(conn, task_id, result)
    db.record_this_invocation(conn, status=db.Stopped())
    conn.commit()


def main(args=None):
    args = sys.argv[1:] if args is None else args
    if len(args) == 0:
        interactive(1)
    elif len(args) == 1:
        interactive(int(args[0]))
    elif len(args) == 2 and args[1] == '--no-db':
        interactive(int(args[0]), use_db=False)
    elif len(args) == 2:
        raise NotImplementedError()
    else:
        assert False


if __name__ == '__main__':
    from importlib.util import find_spec
    if find_spec('hintcheck'):
        import hintcheck
        hintcheck.hintcheck_all_functions()

    main()
