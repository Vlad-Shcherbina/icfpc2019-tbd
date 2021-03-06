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
        return 'insect3 extension'

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        task = GridTask(task)
        game = Game(task)

        if not game.clone_spawn:
            return SolverResult(
                    data=Pass(),
                    expected_score=None,
                    extra=dict(reason='no clone spawns'))
        if not game.inventory['C'] and not game.map_contains_booster('C'):
            return SolverResult(
                    data=Pass(),
                    expected_score=None,
                    extra=dict(reason='no clone boosters'))

        cnt = 0
        while not game.finished():
            cnt += 1
            if cnt % 200 == 0:
                logging.info(f'{len(game.bots)} bots; {game.remaining_unwrapped} unwrapped')

            used_bots = [False for bot in game.bots]
            actions = [None for bot in game.bots]
            orig_bots = game.bots[:]

            if game.clone_spawn and game.inventory['C']:
                logging.info('need spawn')
                df = DistanceField(game.grid)
                df.build(game.clone_spawn)
                dist = df.dist

                best_rank = 1e10
                best_bot = None
                best_action = None
                for bot_index, bot in enumerate(orig_bots):
                    if dist[bot.pos] == 0:
                        continue
                    for d, a in Action.DIRS.items():
                        p = bot.pos + d
                        if not game.grid.in_bounds(p):
                            continue
                        rank = dist[p]
                        if rank < best_rank:
                            best_rank = rank
                            best_bot = bot_index
                            best_action = a
                #assert best_bot is not None
                #game.apply_action(best_action, best_bot)
                if best_bot is not None:
                    actions[best_bot] = best_action
                    used_bots[best_bot] = True

            boosters = [b.pos for b in game.boosters if b.code == 'C']
            if not game.finished() and game.clone_spawn and not game.inventory['C'] and boosters and not all(used_bots):
                df = DistanceField(game.grid)
                df.build(boosters)
                dist = df.dist

                best_rank = 1e10
                best_bot = None
                best_action = None
                for bot_index, bot in enumerate(orig_bots):
                    if used_bots[bot_index]:
                        continue
                    for d, a in Action.DIRS.items():
                        p = bot.pos + d
                        if not game.grid.in_bounds(p):
                            continue
                        rank = dist[p]
                        if rank < best_rank:
                            best_rank = rank
                            best_bot = bot_index
                            best_action = a
                assert best_bot is not None
                actions[best_bot] = best_action
                used_bots[best_bot] = True

            if game.finished():
                break

            df = DistanceField(game.grid)
            starts = list_unwrapped(game._wrapped)
            df.build(starts)
            dist = df.dist

            for bot_index, bot in enumerate(orig_bots):
                if game.finished():
                    break
                if used_bots[bot_index]:
                    game.apply_action(actions[bot_index], bot_index)
                    continue
                if  game.inventory['C'] and bot.pos in game.clone_spawn:
                    game.apply_action(Action.clone(), bot_index)
                    logging.info('clone!!!')
                    continue
                if game.inventory['B'] > 0:
                    logger.info('attach extension')
                    game.apply_action(Action.attach(1, len(game.bots[0].manipulator) - 2))
                    continue

                best_rank = 1e10
                best_action = None
                for d, a in Action.DIRS.items():
                    p = bot.pos + d
                    if not game.grid.in_bounds(p):
                        continue
                    rank = dist[p]
                    for j, bot2 in enumerate(orig_bots):
                        if j < bot_index:
                            d = bot.pos.manhattan_dist(bot2.pos)
                            rank += 10 * max(0, 30 - d)
                    if rank < best_rank:
                        best_rank = rank
                        best_action = a
                assert best_action is not None

                game.apply_action(best_action, bot_index)

        expected_score = score = game.finished()
        extra = dict(final_bots=len(game.bots))
        return SolverResult(
            data=compose_actions(game.get_actions()),
            expected_score=expected_score,
            extra=extra)


def main():
    # s = utils.get_problem_raw(1)
    s = Path(utils.project_root() / 'tasks' / 'part-0-mock' / 'prob-2003.desc').read_text()

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
