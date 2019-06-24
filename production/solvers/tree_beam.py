import logging
logger = logging.getLogger(__name__)
import time
from pathlib import Path
from typing import List, Tuple, Any
from collections import deque
from copy import deepcopy

from production import utils
from production.data_formats import *
from production.geom import poly_bb, rasterize_poly, visible
from production.solvers.interface import *
from production.game import Game, BacktrackingGame, InvalidActionException
from pprint import pprint


def bfs_extract_path(node, visited):
    path = []
    while node is not None:
        path.append(node)
        node = visited[node]
    path.reverse()
    return path


def calculate_distance_field(game: Game, source: Pt, target: Pt):
    # Calculate and return a distance field from the target, over visited cells only
    sentinel = object()
    front = deque([source, sentinel])
    distfield = {source: 0}
    generation = 1
    found = False
    while front:
        p = front.popleft()
        if p == sentinel:
            if found:
                break
            assert front
            generation += 1
            front.append(sentinel)
            continue

        for d in Action.DIRS.keys():
            p2 = p + d
            if (    p2 not in distfield and
                    game.in_bounds(p2) and
                    game.is_passable(p2)):
                distfield[p2] = generation
                front.append(p2)
                if p2 == target:
                    found = True
    return distfield


def print_distfield(game, distfield):
    g = CharGrid(game.height, game.width, '.')
    for p, d in distfield.items():
        g[p] = chr(ord('0') + d)
    print(g.grid_as_text())


def get_action(game: Game, max_depth: int, distfield, target: Pt):
    game = BacktrackingGame(game, game.bots[0])
    t = time.perf_counter()

    # print(game.bots[0].pos, target)
    # g = CharGrid(game.height, game.width, '.')
    # for p, d in distfield.items():
    #     g[p] = chr(ord('0') + d)
    # print(g.grid_as_text())

    # if distance_to_target > 5:
    #     # HACK: in large wrapped spaces don't think too hard
    #     max_depth = min(3, max_depth)

    logging.info(f'turn={game.turn} pos={game.bot.pos} target={target} d={game.bot.pos.manhattan_dist(target)} unwrapped={game.remaining_unwrapped}')

    scores = {}
    best_score, best_action = -99999, None
    nodes_evaluated = 0

    def recur(game: Game, depth = 0, first_action=None):
        # process attempted new state at the beginning of the recursive call
        nonlocal nodes_evaluated, best_score, best_action
        nodes_evaluated += 1

        bot = game.bot

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

        # hack: collect boosters we want to use
        booster = [b for b in game.game.boosters if b.pos == bot.pos]
        if booster:
            [booster] = booster
            if booster.code in 'B':
                score += 1000
                success = True

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
                recur(game.apply_action(action), depth + 1, first_action if first_action else action)
        recur(game.apply_action(Action.turnCW()), depth + 1, first_action if first_action else Action.turnCW())
        recur(game.apply_action(Action.turnCCW()), depth + 1, first_action if first_action else Action.turnCCW())
    recur(game)
    oldt, t = t, time.perf_counter()
    logging.info(f'{best_action} {best_score}; evaluated {nodes_evaluated} nodes in {t - oldt:0.3f}')
    return best_action


#    o
# ~~~~~~
def attach_lined(game: Game, botindex = 0):
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

    return Action.attach(candidate.x, candidate.y)


@dataclass
class Treenode:
    pos: Pt
    parent: Any
    children: Any = dataclasses.field(default_factory=list)
    # counts include this node
    children_cnt: int = 0
    wrapped_children_cnt: int = 0

    def fill_stats(self, game: Game):
        self.children_cnt = 1
        self.wrapped_children_cnt = game.is_wrapped(self.pos)
        for c in self.children:
            cnt, wcnt = c.fill_stats(game)
            self.children_cnt += cnt
            self.wrapped_children_cnt += wcnt
        return self.children_cnt, self.wrapped_children_cnt

    def wrap(self):
        self.wrapped_children_cnt += 1
        assert self.wrapped_children_cnt <= self.children_cnt
        if self.parent:
            self.parent.wrap()

    def get_unwrapped_child(self):
        if self.wrapped_children_cnt == self.children_cnt:
            return None
        for c in self.children:
            res = c.get_unwrapped_child()
            if res:
                return res
        assert self.wrapped_children_cnt == self.children_cnt - 1
        return self

    def get_next_unwrapped(self):
        res = self.get_unwrapped_child()
        if res:
            return res
        return self.parent.get_next_unwrapped()


def calculate_spanning_tree(game: Game, pos: Pt):
    front = deque([pos])
    visited = {pos: Treenode(pos, None)}
    found = None

    while front:
        p = front.popleft()
        pnode = visited[p]
        for d in Action.DIRS.keys():
            p2 = p + d
            if (    p2 not in visited
                    and game.in_bounds(p2)
                    and game.is_passable(p2)):
                visited[p2] = Treenode(p2, pnode)
                pnode.children.append(visited[p2])
                front.append(p2)

    visited[pos].fill_stats(game)
    return visited


def solve(task: Task, max_depth) -> Tuple[int, List[List[Action]], dict]:
    task = GridTask(task)

    game = Game(task)
    st_root = game.bots[0].pos
    spanning_tree = calculate_spanning_tree(game, st_root)
    target = None

    while not game.finished():
        while game.inventory['B'] > 0:
            logger.info('attach extension')
            action = attach_lined(game)
            wrap_updates = game.apply_action(action)
            for p in wrap_updates:
                assert game.is_wrapped(p)
                spanning_tree[p].wrap()

        bot = game.bots[0]
        if target is None:
            target = spanning_tree[bot.pos].get_next_unwrapped().pos
            distfield = calculate_distance_field(game, target, bot.pos)
            #print_distfield(game, distfield)

        action = get_action(game, max_depth, distfield, target)
        assert action
        wrap_updates = game.apply_action(action)
        for p in wrap_updates:
            assert game.is_wrapped(p)
            spanning_tree[p].wrap()

        if game.is_wrapped(target):
            target = None

    score = game.finished()
    logger.info(game.inventory)

    extra = dict(final_manipulators = len(game.bots[0].manipulator))

    return score, game.get_actions(), extra


class TreeBeamSolver(Solver):
    def __init__(self, args: List[str]):
        [] = args
        self.max_depth = 5

    def scent(self) -> str:
        return f'tree beam v2 d={self.max_depth}'

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        expected_score, actions, extra = solve(task, self.max_depth)
        return SolverResult(
            data=compose_actions(actions),
            expected_score=expected_score,
            extra=extra)


def main():
    problem = 10
    sol = TreeBeamSolver([]).solve(utils.get_problem_raw(problem))
    print(sol.extra)
    sol = sol.data
    print(len(sol), 'time units')
    sol_path = Path(utils.project_root() / 'outputs' / f'tree_beam-{problem}.sol')
    sol_path.write_text(sol)
    print('result saved to', sol_path)


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    # from importlib.util import find_spec
    # if find_spec('hintcheck'):
    #     import hintcheck
    #     hintcheck.hintcheck_all_functions()

    main()
