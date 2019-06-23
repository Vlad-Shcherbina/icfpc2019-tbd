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
from production.cpp_grid.cpp_grid_ext import pathfind
# from production.examples.cpp_demo import sample


# how many moves can be traded for wrapped squares
# total_cost = moves - wrapped_squares * wrap_tradeoff
WRAP_TRADEOFF = 0.5
BOOST_TRADEOFF = 5

SEARCH_RADIUS = 5


def search_boosts(game: Game, pos: Pt, allowed='B'):
    available = []
    for dx in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
        for dy in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
            p = pos + Pt(dx, dy)
            if not game.grid.in_bounds(p):
                continue
            for b in game.boosters:
                if b.pos != p: continue
                if b.code not in allowed: continue
                available.append(b)
    return available


 #    o
 # ~~~~~~  <- symmetrical attach
def attach_manip(game: Game, botindex = 0):
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
    game.apply_action(Action.attach(candidate.x, candidate.y))


# it's copy-pasted from greedy.py with only rotation addition
def solve(game, bestscore=None) -> Tuple[Optional[int], List[List[Action]], dict]:
    cnt = 0

    while not game.finished():
        cnt += 1
        if cnt % 1000 == 0:
            logging.info(f'{len(game.unwrapped)} unwrapped')

        prev = {game.bots[0].pos: None}
        frontier = [game.bots[0].pos]
        while frontier:
            best_rank = 0
            dst = None
            for p in frontier:
                rank = 0
                for m in game.bots[0].manipulator:
                    q = p + m
                    # TODO: visibility and bounds check
                    if (game.in_bounds(q) and
                        game.grid[q] == '.' and
                        q in game.unwrapped and
                        visible(game.grid, q, p)):
                        rank += 1
                if rank > best_rank:
                    best_rank = rank
                    dst = p
            if dst is not None:
                break

            new_frontier = []
            for p in frontier:
                for d in Action.DIRS.keys():
                    p2 = p + d
                    if (p2 not in prev and 
                        game.in_bounds(p2) 
                        and game.grid[p2] == '.'):

                        prev[p2] = p
                        new_frontier.append(p2)
            frontier = new_frontier

        assert dst is not None
        assert dst != game.bots[0].pos


        pf = pathfind(game.grid, game.bots[0].pos, dst)

        for p in pf:
            boosts = search_boosts(game, p, 'B')
            for b in boosts:
                new_pf = (pathfind(game.grid, game.bots[0].pos, b.pos)
                          + pathfind(game.grid, b.pos, dst)[1:])
                if len(new_pf) - 1 - BOOST_TRADEOFF < len(pf):
                    pf = new_pf

        path = [Action.DIRS[pf[i + 1] - pf[i]] for i in range(len(pf) - 1)]




        for a in path:
            game.apply_action(a)
        if bestscore is not None and game.turn >= bestscore:
            return None, [], {}

        if game.inventory['B'] > 0:
            logger.info('attach extension')
            attach_manip(game, 0)


    score = game.finished()
    logger.info(game.inventory)

    extra = dict(final_manipulators = len(game.bots[0].manipulator))

    return score, game.get_actions(), extra


# ---------------------------------------------------------- #

class BoostySolver(Solver):
    def __init__(self, args: List[str]):
        if len(args) == 2:
            WRAP_TRADEOFF = float(args[0])
            BOOST_TRADEOFF = float(args[1])


    def scent(self) -> str:
        return 'boosty 0.1'

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        min_score = None

        for turns in ([],
                      [Action.turnCCW()],
                      [Action.turnCCW(), Action.turnCCW()],
                      [Action.turnCW()]):
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
    s = Path(utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01.desc').read_text()
    task = Task.parse(s)
    _, sol, _ = solve(Game(GridTask(task)))
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
