import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from typing import List, Tuple

from production import utils
from production.data_formats import *
from production.geom import poly_bb, rasterize_poly, visible
from production.solvers.interface import *
from production.game import Game


def solve(task: Task) -> Tuple[int, List[List[Action]], dict]:
    task = GridTask(task)

    game = Game(task)

    cnt = 0
    while not game.finished():
        cnt += 1
        if cnt % 1000 == 0:
            logging.info(f'{len(game.unwrapped)} unwrapped')
        prev = {game.bots[0].pos: None}
        frontier = [game.bots[0].pos]
        while frontier:
            dst = None
            for p in frontier:
                for m in game.bots[0].manipulator:
                    q = p + m
                    # TODO: visibility and bounds check
                    if (game.in_bounds(q) and
                        game.grid[q] == '.' and
                        q in game.unwrapped and
                        visible(game.grid, q, p)):
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

        path = []
        p = dst
        while p != game.bots[0].pos:
            d = p - prev[p]
            path.append(Action.DIRS[d])
            p = prev[p]
            assert p is not None
        path.reverse()
        for a in path:
            game.apply_action(a)

        if game.inventory['B'] > 0:
            logger.info('attach extension')
            game.apply_action(Action.attach(1, len(game.bots[0].manipulator) - 2))

    score = game.finished()
    logger.info(game.inventory)

    extra = dict(final_manipulators = len(game.bots[0].manipulator))

    return score, game.get_actions(), extra


class GreedySolver(Solver):
    def __init__(self, args: List[str]):
        [] = args

    def scent(self) -> str:
        return 'greedy 2'

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        expected_score, actions, extra = solve(task)
        return SolverResult(
            data=compose_actions(actions),
            expected_score=expected_score,
            extra=extra)


def main():
    s = Path(utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01.desc').read_text()
    task = Task.parse(s)
    sol = solve(task)
    sol = compose_actions(sol)
    print(sol)
    print(len(sol), 'time units')
    sol_path = Path(utils.project_root() / 'outputs' / 'example-01-greedy.sol')
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
