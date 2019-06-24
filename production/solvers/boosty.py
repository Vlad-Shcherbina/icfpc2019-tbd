import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from typing import List, Tuple, Optional
from copy import deepcopy

from production import utils
from production.data_formats import *
from production.geom import poly_bb, rasterize_poly, visible
from production.solvers.interface import *
from production.game import Game
from production.solvers.greedy import GreedySolver
from production.cpp_grid import Pt, CharGrid
from production.cpp_grid.cpp_grid_ext import boostfind


from time import time

# how many moves can be traded for wrapped squares
# total_cost = moves - wrapped_squares * wrap_penalty
WRAP_PENALTY = 20
BOOST_TRADEOFF = 5

SEARCH_RADIUS = 5
ALLOWED = 'B'

 #    o
 # ~~~~~~  <- symmetrical attach
def attach_manip(game: Game, bot_area, botindex = 0):
    bot = game.bots[botindex]
    d = None
    for d in Action.DIRS.keys():
        if d in bot.manipulator:
            break
    assert d is not None
    ccw = d.rotated_ccw()

    i = 0
    while True:
        candidate = d + ccw * i
        if candidate not in bot.manipulator:
            break
        candidate = d - ccw * i
        if candidate not in bot.manipulator:
            break
        i += 1

    for d in Action.DIRS.keys():
        if candidate +  d not in bot_area:
            bot_area.append(candidate + d)
    game.apply_action(Action.attach(candidate.x, candidate.y))


def update_wrapped(grid: CharGrid, wrapped: CharGrid, bot):
    wrapped[bot.pos] = '+'
    for m in bot.manipulator:
        if wrapped.in_bounds(bot.pos + m) and visible(grid, bot.pos, bot.pos + m):
            wrapped[bot.pos + m] = '+'


def is_frontier(p: Pt, grid, wrapped):
    if not grid.in_bounds(p):
        return False

    if wrapped[p] != '.':
        return False

    count = {'.' : 0, '+' : 0, '#' : 0}
    for d in [Pt(0, 0)] + list(Action.DIRS.keys()):
        if wrapped.in_bounds(p + d):
            count[wrapped[p + d]] += 1
    return count['.'] > 0 and count['+'] > 0


def clean_frontier(frontier, game, wrapped):
    return [f for f in frontier if is_frontier(f, game.grid, wrapped)]
    

def solve(game, bestscore=None) -> Tuple[Optional[int], List[List[Action]], dict]:
    cnt = 0
    wrapped = CharGrid(game.grid)
    bot = game.bots[0]
    update_wrapped(game.grid, wrapped, bot)

    bot_area = []
    bot_area.append(Pt(0, 0))
    for m in bot.manipulator:
        if m not in bot_area:
            bot_area.append(m)
        for d in Action.DIRS.keys():
            if (m + d) not in bot_area:
                bot_area.append(m + d)

    # print(bot_area)

    frontier = []
    for m in bot_area:
        if bot.pos + m not in frontier:
            frontier.append(bot.pos + m)
    frontier = clean_frontier(frontier, game, wrapped)

    def remove(f, rm):
        for i in range(len(f)):
            if f[i] == rm:
                f[i] = f[-1]
                f.pop()
                return

    while not game.finished():
        cnt += 1
        if cnt % 1000 == 0:
            logging.info(f'{game.remaining_unwrapped} unwrapped')

        boosts = [b.pos for b in game.boosters if b.code in ALLOWED]
        penalty = (game.grid.height + game.grid.width) * 2

        path = boostfind(game.grid, wrapped, bot.pos, bot.manipulator,
                         frontier, boosts, BOOST_TRADEOFF, penalty)

        assert len(path) > 1
        if len(path) > 2:
            path.pop()


        cmds = [Action.DIRS[path[i + 1] - path[i]] for i in range(len(path) - 1)]
        for a in cmds:
            game.apply_action(a)
            update_wrapped(game.grid, wrapped, bot)
        if bestscore is not None and game.turn >= bestscore:
            return None, [], {}

        if game.inventory['B'] > 0:
            logger.info('attach extension')
            attach_manip(game, bot_area, 0)

        checked = []
        for p in path:
            for m in bot_area:
                pm = p + m
                if pm in checked:
                    continue

                if is_frontier(pm, game.grid, wrapped):
                    if pm not in frontier:
                        frontier.append(pm)
                else:
                    remove(frontier, pm)
                checked.append(pm)

        remove(frontier, bot.pos)

    score = game.finished()
    logger.info(game.inventory)

    extra = dict(final_manipulators = len(game.bots[0].manipulator))

    return score, game.get_actions(), extra


# ---------------------------------------------------------- #

class BoostySolver(Solver):
    def __init__(self, args: List[str]):
        if len(args) == 1:
            if args[0] == 'rotate':
                self.turns = True
            elif args[0] == 'straight':
                self.turns = False
            else:
                assert False, args
        elif len(args) == 0:
            self.turns = True
        else:
            assert False, args


    def scent(self) -> str:
        return 'boosty 1 ' + ('rotate' if self.turns else 'straight')

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        min_score = None
        min_actions = []
        min_extra = {}

        turnlist = [[]]
        if self.turns:
            turnlist += [[Action.turnCCW()],
                         [Action.turnCCW(), Action.turnCCW()],
                         [Action.turnCW()]]

        # turnlist = [[Action.turnCW()]]

        for turns in turnlist:
            game = Game(GridTask(task))
            for t in turns:
                game.apply_action(t)

            expected_score, actions, extra = solve(game, min_score)
            if expected_score is None:
                # solution has exceeded the best score and stopped
                continue
            if min_score is None or expected_score < min_score:
                min_score, min_actions, min_extra = expected_score, actions, extra
        return SolverResult(
            data=compose_actions(min_actions),
            expected_score=min_score,
            extra=min_extra)


def main():
    s = Path(utils.project_root() / 'tasks' / 'part-1-initial' / 'prob-145.desc').read_text()
    solver = BoostySolver([])
    t = time()
    sol = solver.solve(s)
    print(f'time elapsed: {time() - t:.4}')
    print(sol)
    task = Task.parse(s)
    score, sol, _ = solve(Game(GridTask(task)))
    print("score:", score)
    sol = compose_actions(sol)
    print(sol)
    print(len(sol), 'time units')
    sol_path = Path(utils.project_root() / 'outputs' / 'example-01-boosty.sol')
    sol_path.write_text(sol)
    print('result saved to', sol_path)


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    from importlib.util import find_spec
    if find_spec('hintcheck'):
        import hintcheck
        hintcheck.hintcheck_all_functions()

    main()    
