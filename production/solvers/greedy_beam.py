import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from typing import List, Tuple
from collections import deque

from production import utils
from production.data_formats import *
from production.geom import poly_bb, rasterize_poly, visible
from production.solvers.interface import *
from production.game import Game


def bfs_extract_path(node, visited):
    path = []
    while node is not None:
        path.append(node)
        node = visited[node]
    path.reverse()
    return path


def find_a_target(game: Game, pos: Pt):
    # bfs until we find an unwrapped cell, return it and visited
    front = deque([pos])
    visited = {pos: None}
    while front:
        p = front.popleft()
        for d in Action.DIRS.keys():
            p2 = p + d
            if (    p2 not in visited
                    and game.in_bounds(p2)
                    and game.grid[p2] == '.'):
                visited[p2] = p
                if not game.is_wrapped(p2):
                    return p2, visited
                front.append(p2)
    return None, None


def calculate_distance_field(game: Game, target: Pt, visited):
    # Calculate and return a distance field from the target, over visited cells only
    sentinel = object()
    generation = 0
    target_generation = len(bfs_extract_path(target, visited))
    # path = [0, 1]; target_generation = 2, break when greater.
    front = deque([pos, sentinel])
    distfield = {pos: generation}
    while front:
        p = front.popleft()
        if p == sentinel:
            generation += 1
            if generation > target_generation:
                break
            continue
        for d in Action.DIRS.keys():
            p2 = p + d
            if p2 not in distfield and p2 in visited:
                distfield[p2] = p
                front.append(p2)
    return distfield


def get_action(game: Game, pos: Pt):
    target, visited = find_a_target(game, pos)
    distfield = calculate_distance_field(game, target, visited)

    def apply_action(game: Game, action: Action):
        game = deepcopy(game)
        game.apply_action(action)
        return game

    scores = {}

    def recur(game: Game, depth: int):
        bot = game.bots[0]
        for dp, action in Action.DIRS:
            np = bot.pos + dp

            # never move backward
            if distfield.get(np, 99999) > distfield[bot.pos]:
                continue

            key = (np, bot.int_direction)
            



def solve(task: Task) -> Tuple[int, List[List[Action]], dict]:
    task = GridTask(task)

    game = Game(task)

    cnt = 0
    while not game.finished():
        cnt += 1
        if cnt % 1000 == 0:
            logging.info(f'{len(game.unwrapped)} unwrapped')

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
