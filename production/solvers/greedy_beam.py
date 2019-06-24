import logging
logger = logging.getLogger(__name__)
import time
from pathlib import Path
from typing import List, Tuple
from collections import deque
from copy import deepcopy

from production import utils
from production.data_formats import *
from production.geom import poly_bb, rasterize_poly, visible
from production.solvers.interface import *
from production.game import Game, InvalidActionException


def bfs_extract_path(node, visited):
    path = []
    while node is not None:
        path.append(node)
        node = visited[node]
    path.reverse()
    return path


def find_nearest_unwrapped(game: Game, pos: Pt) -> Tuple[Pt, dict]:
    # bfs until we find an unwrapped cell, return it and visited
    sentinel = object()
    front = deque([pos, sentinel])
    visited = {pos: None}
    found = None

    while front:
        p = front.popleft()
        if p == sentinel:
            if found:
                # return only now, so that visited is a complete set of points reachable in n steps
                return found, visited
            if not front:
                break
            front.append(sentinel)
            continue

        for d in Action.DIRS.keys():
            p2 = p + d
            if (    p2 not in visited
                    and game.in_bounds(p2)
                    and game.grid[p2] == '.'):
                visited[p2] = p
                if not game.is_wrapped(p2):
                    found = p2
                front.append(p2)
    return None, visited


def calculate_distance_field(game: Game, target: Pt, visited):
    # Calculate and return a distance field from the target, over visited cells only
    sentinel = object()
    generation = 0
    target_generation = len(bfs_extract_path(target, visited))
    # path = [0, 1]; target_generation = 2, break when greater.
    front = deque([target, sentinel])
    distfield = {target: generation}
    while front:
        p = front.popleft()
        if p == sentinel:
            generation += 1
            if generation > target_generation:
                break
            if not front:
                break
            front.append(sentinel)
            continue

        for d in Action.DIRS.keys():
            p2 = p + d
            if p2 not in distfield and p2 in visited:
                distfield[p2] = generation
                front.append(p2)
    return distfield


def get_action(game: Game, max_depth: int):
    t = time.perf_counter()
    target, visited = find_nearest_unwrapped(game, game.bots[0].pos)
    distfield = calculate_distance_field(game, target, visited)
    distance_to_target = target.manhattan_dist(game.bots[0].pos)

    if distance_to_target > 5:
        # HACK: in large wrapped spaces don't think too hard
        max_depth = min(3, max_depth)

    oldt, t = t, time.perf_counter()
    logging.info(f'turn={game.turn} unwrapped={game.remaining_unwrapped} found target d={distance_to_target} and computed distfield in {t - oldt:0.3f}')

    def apply_action(game: Game, action: Action):
        game = deepcopy(game)
        game.apply_action(action)
        return game

    scores = {}
    best_score, best_action = -99999, None
    nodes_evaluated = 0

    def recur(game: Game, depth = 0, first_action=None):
        # process attempted new state at the beginning of the recursive call
        nonlocal nodes_evaluated, best_score, best_action
        nodes_evaluated += 1

        bot = game.bots[0]

        success = game.is_wrapped(target)
        delay_penalty = -2

        # game.turn and distfield[bot.pos] essentially count the same thing and negate each other,
        # but:
        # - for searches terminated due to max_depth turn is irrelevant because it's the same, so
        #   they automatically optimize for lower distfield
        # - for successfully terminated searches we ignore distfield and turn becomes relevant
        # - don't reward success beyond the naturally better score because of the above penalties
        # - only compare best scores for completed searchesso that the first point holds (otherwise
        #   node score can be worse than that of its children)
        score = -game.remaining_unwrapped
        score += game.turn * delay_penalty
        if not success:
            score += distfield[bot.pos] * delay_penalty

        key = (bot.pos, bot.int_direction)

        if key in scores and scores[key] > score:
            return

        scores[key] = score

        if success or depth >= max_depth:
            if first_action and score > best_score:
                best_action = first_action
                best_score = score
            return

        for dp, action in Action.DIRS.items():
            # never move backward, also means we never run into walls
            if distfield.get(bot.pos + dp, 99999) <= distfield[bot.pos]:
                recur(apply_action(game, action), depth + 1, first_action if first_action else action)
        recur(apply_action(game, Action.turnCW()), depth + 1, first_action if first_action else Action.turnCW())
        recur(apply_action(game, Action.turnCCW()), depth + 1, first_action if first_action else Action.turnCCW())
    recur(game)
    oldt, t = t, time.perf_counter()
    logging.info(f'{best_action} {best_score}; evaluated {nodes_evaluated} nodes in {t - oldt:0.3f}')
    return best_action


def solve(task: Task, max_depth) -> Tuple[int, List[List[Action]], dict]:
    task = GridTask(task)

    game = Game(task)

    while not game.finished():
        while game.inventory['B'] > 0:
            logger.info('attach extension')
            game.apply_action(Action.attach(1, len(game.bots[0].manipulator) - 2))

        action = get_action(game, max_depth)
        game.apply_action(action)

    score = game.finished()
    logger.info(game.inventory)

    extra = dict(final_manipulators = len(game.bots[0].manipulator))

    return score, game.get_actions(), extra


class GreedyBeamSolver(Solver):
    def __init__(self, args: List[str]):
        [] = args
        self.max_depth = 5

    def scent(self) -> str:
        return f'greedy beam d={self.max_depth}'

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        expected_score, actions, extra = solve(task, self.max_depth)
        return SolverResult(
            data=compose_actions(actions),
            expected_score=expected_score,
            extra=extra)


def main():
    problem = 11
    sol = GreedySolver([]).solve(utils.get_problem_raw(problem))
    sol = sol.data
    print(len(sol), 'time units')
    sol_path = Path(utils.project_root() / 'outputs' / f'beam-{problem}.sol')
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
