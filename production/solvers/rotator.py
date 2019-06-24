import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from typing import List, Tuple, Optional

from production import utils
from production.data_formats import *
from production.solvers.interface import *
from production.geom import poly_bb, rasterize_poly
from production.cpp_grid.cpp_grid_ext import manipulators_will_wrap
from production.game import Game
from production.solvers.greedy import GreedySolver


def turn_pt(p: Pt, turn: str) -> Pt:
    assert len(turn) == 1, turn
    if turn == 'E':
        return p.rotated_cw()
    elif turn == 'Q':
        return p.rotated_ccw()
    else:
        assert False, turn


# it's copy-pasted from greedy.py with only rotation addition
def solve(task: Task, turns: str, bestscore=None) -> Tuple[Optional[int], List[List[Action]], dict]:
    task = GridTask(task)

    game = Game(task)

    cnt = 0

    for t in turns:
        game.apply_action(Action.simple(t))

    while not game.finished():
        cnt += 1
        if cnt % 1000 == 0:
            logging.info(f'{game.remaining_unwrapped} unwrapped')
        extensions = {b.pos for b in game.boosters if b.code == 'B'}
        prev = {game.bots[0].pos: None}
        frontier = [game.bots[0].pos]
        while frontier:
            best_rank = 0
            dst = None
            for p in frontier:
                rank = 0
                if p in extensions:
                    rank += 5
                rank += len(manipulators_will_wrap(game.grid, game._wrapped, p, game.bots[0].manipulator))
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
        if bestscore is not None and game.turn >= bestscore:
            return None, [], {}

        if game.inventory['B'] > 0:
            logger.info('attach extension')
            attach_to = Pt(1, len(game.bots[0].manipulator) - 2)
            for t in turns:
                attach_to = turn_pt(attach_to, t)
            game.apply_action(Action.attach(attach_to.x, attach_to.y))

    score = game.finished()
    logger.info(game.inventory)

    extra = dict(final_manipulators = len(game.bots[0].manipulator))

    return score, game.get_actions(), extra



class RotatorSolver(Solver):
    def __init__(self, args: List[str]):
        [] = args

    def scent(self) -> str:
        return 'rotator 1 bonus'

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        min_score = None

        for turns in ('', 'E', 'EE', 'Q'):
            expected_score, actions, extra = solve(task, turns, min_score)
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
    s = Path(utils.project_root() / 'tasks' / 'part-1-initial' / 'prob-002.desc').read_text()
    task = Task.parse(s)
    _, sol, _ = solve(task, '')
    sol = compose_actions(sol)
    print(sol)
    print(len(sol), 'time units')
    sol_path = Path(utils.project_root() / 'outputs' / 'example-01-rotator.sol')
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
