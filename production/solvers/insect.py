import logging
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import List, Tuple

from production import utils
from production.data_formats import *
from production.geom import poly_bb, rasterize_poly
from production.solvers.interface import *
from production.game import Game
from production.cpp_grid import CharGrid
from production.cpp_grid.cpp_grid_ext import DistanceField, list_unwrapped
from production.golden import validate


class InsectSolver(Solver):
    def __init__(self, args: List[str]):
        [] = args

    def scent(self) -> str:
        return 'insect1'

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        task = GridTask(task)
        game = Game(task)
        while not game.finished():
            logging.info(f'{game.remaining_unwrapped} unwrapped')
            starts = list_unwrapped(game._wrapped)
            df = DistanceField(game.grid)
            df.build(starts)
            dist = df.dist

            best_rank = 1e10
            best_action = None
            for d, a in Action.DIRS.items():
                p = game.bots[0].pos + d
                if not game.grid.in_bounds(p):
                    continue
                rank = dist[p]
                if rank < best_rank:
                    best_rank = rank
                    best_action = a
            assert best_action is not None
            game.apply_action(best_action)

        expected_score = score = game.finished()
        extra = {}
        return SolverResult(
            data=compose_actions(game.get_actions()),
            expected_score=expected_score,
            extra=extra)


def main():
    s = utils.get_problem_raw(1)
    solver = InsectSolver([])
    result = solver.solve(s)
    logging.info(result)
    logging.info('validating...')
    vr = validate.run(s, result.data)
    logging.info(vr)
    # grid = [
    #     '# # # # # # #',
    #     '# . . . . . #',
    #     '# . . . . . #',
    #     '# . . . . . #',
    #     '# . . . . . #',
    #     '# # # # # # #',
    # ]
    # grid = [row.replace(' ', '') for row in grid]
    # grid = CharGrid(grid)
    # print(grid)

    # df = DistanceField(grid)
    # df.build([Pt(3, 2), Pt(4, 1)])
    # dist = df.dist
    # for y in range(dist.height):
    #     for x in range(dist.width):
    #         print(f'{dist[Pt(x, y)]:>4}', end=' ')
    #     print()
    # print(df.dist)


if __name__ == '__main__':
    from importlib.util import find_spec
    if find_spec('hintcheck'):
        import hintcheck
        hintcheck.hintcheck_all_functions()

    main()
