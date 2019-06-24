import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from typing import List, Tuple, Optional

from production import utils
from production.data_formats import *
from production.solvers.interface import *
from production.geom import poly_bb, rasterize_poly
from production.cpp_grid.cpp_grid_ext import visible
from production.game import Game
from production.solvers.greedy import GreedySolver


# -------------------- manip configurations


#    o
# ~~~~~~
def attach_lined(game: Game, extras: dict, botindex = 0):
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


#  ~~~~
#  ~  ~
# o~  ~
#  ~~~~
def attach_squared(game: Game, extras: dict, botindex = 0):
    bot = game.bots[botindex]
    d = None
    for d in Action.DIRS.keys():
        if d in bot.manipulator:
            break
    assert d is not None

    ccw = d.rotated_ccw()
    shoulder = extras['booster_count'] // 4

    candidate = None
    if candidate is None:
        i = 0
        while i <= shoulder / 2:
            candidate = d + ccw * i
            if candidate not in bot.manipulator:
                break
            candidate = d - ccw * i
            if candidate not in bot.manipulator:
                break
            i += 1
        else:
            candidate = None

    if candidate is None:
        left = d + ccw * (shoulder // 2)
        right = d - ccw * (shoulder // 2)
        i = 1
        while i < shoulder:
            candidate = left + d * i
            if candidate not in bot.manipulator:
                break
            candidate = right + d * i
            if candidate not in bot.manipulator:
                break
            i += 1
        else:
            candidate = None

    if candidate is None:
        left = d * shoulder + ccw * (shoulder // 2)
        right = d * shoulder - ccw * (shoulder // 2)
        i = 1
        while i < shoulder / 2:
            candidate = left - ccw * i
            if candidate not in bot.manipulator:
                break
            candidate = right + ccw * i
            if candidate not in bot.manipulator:
                break
            i += 1
        else:
            candidate = None

    if candidate is None:
        i = 1
        while d * (-i) in bot.manipulator:
            i += 1
        candidate = d * (-i)

    game.apply_action(Action.attach(candidate.x, candidate.y))


# -------------------------- solve ----------------------------------


def solve(game: Game, params: dict) -> Tuple[Optional[int], List[List[Action]], dict]:
    cnt = 0

    params['booster_count'] = sum(1 for b in game.boosters if b.code == 'B')
    map_center = Pt(game.grid.width // 2, game.grid.height // 2)
    teleport_list = []

    while not game.finished():
        cnt += 1
        if cnt % 1000 == 0:
            logging.info(f'{game.remaining_unwrapped} unwrapped')

        bot = game.bots[0]
        extensions = {b.pos for b in game.boosters if b.code in params['boostlist']}
        prev = { bot.pos: None }
        frontier = [bot.pos]

        # searching target
        depth = 0
        while frontier:
            best_rank = 0
            dst = None
            for p in frontier:
                rank = 0
                if p in extensions:
                    rank += 5
                for m in bot.manipulator:
                    q = p + m
                    if (game.in_bounds(q) and
                        game.grid[q] == '.' and
                        not game.is_wrapped(q) and
                        visible(game.grid, q, p)):
                        rank += 1
                if rank > best_rank:
                    best_rank = rank
                    dst = p
            if dst is not None:
                break

            new_frontier = []
            if depth == 0 and 'R' in params['boostlist']:
                new_frontier = teleport_list[:]
                for p in new_frontier:
                    prev[p] = bot.pos

            for p in frontier:
                for d in Action.DIRS.keys():
                    p2 = p + d
                    if (p2 not in prev and 
                        game.in_bounds(p2) 
                        and (game.grid[p2] == '.'
                             or bot.drill_timer - depth > 0)
                        ):

                        prev[p2] = p
                        new_frontier.append(p2)
            frontier = new_frontier
            depth += 1

        assert dst is not None
        assert dst != bot.pos

        # teleport
        if 'R' in params['boostlist'] and game.inventory['R'] > 0:
            if map_center.manhattan_dist(bot.pos) < map_center.manhattan_dist(dst):
                game.apply_action(Action.reset())
                logger.info('reset teleport')
                teleport_list.append(bot.pos)

        # gathering path
        path = []
        p = dst
        while p != bot.pos:
            d = p - prev[p]
            if d not in Action.DIRS.keys():
                assert 'R' in params['boostlist'] and p in teleport_list
                path.append(Action.teleport(p.x, p.y))
                logger.info('teleport away')
            else:
                path.append(Action.DIRS[d])
            p = prev[p]
            assert p is not None
        path.reverse()

        assert depth == len(path), (depth, len(path))

        for a in path:
            game.apply_action(a)
        if params['best score'] is not None and game.turn >= params['best score']:
            return None, [], {}

        # boosters
        if game.inventory['B'] > 0:
            logger.info('attach extension')
            params['attach func'](game, params, 0)

        if 'L' in params['boostlist'] and game.inventory['L'] > 0:
            logger.info('use drill')
            game.apply_action(Action.drill())



    score = game.finished()
    logger.info(game.inventory)

    extra = dict(final_manipulators = len(game.bots[0].manipulator))

    return score, game.get_actions(), extra


manip_configs = { 'lined' : attach_lined, 'squared' : attach_squared }

# ------------------------ driller -----------------------------------


class TweakerSolver(Solver):

    ''' args:
        manipconf: [lined | squared] - lined if omitted
        driller: [drill | no-drill]  - drill if omitted
        teleport: [teleport | no-teleport] - teleport if omitted
    ''' 
    def __init__(self, args: List[str]):
        self.manipconf = 'lined'
        self.drill = True
        self.teleport = True

        if len(args) >= 1:
            assert args[0] in manip_configs.keys(), args[0]
            self.manipconf = args[0]
        if len(args) >= 2:
            assert args[1] in ('drill', 'no-drill'), args[1]
            self.drill = args[1] == 'drill'
        if len(args) >= 3:
            assert args[2] in ('teleport', 'no-teleport')
            self.teleport = args[2] == 'teleport'


    def scent(self) -> str:
        return ('tweaker 1 ' 
                + self.manipconf
                + (' drill' if self.drill else '')
                + (' teleport' if self.teleport else ''))

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        min_score = None
        # min_actions = []
        # min_extra = {}

        turnlist = { 'Eastborne' : [],
                     'Nordish' : [Action.turnCCW()],
                     'Westerling' : [Action.turnCCW(), Action.turnCCW()],
                     'Southerner' : [Action.turnCW()]}

        params = {}
        params['boostlist'] = 'B'
        if self.drill:
            params['boostlist'] += 'L'
        if self.teleport:
            params['boostlist'] += 'R'

        params['attach func'] = manip_configs[self.manipconf]

        for direction in turnlist:
            logger.info(f'{direction} started working')
            params['best score'] = min_score

            game = Game(GridTask(task))
            for t in turnlist[direction]:
                game.apply_action(t)

            expected_score, actions, extra = solve(game, params)
            logger.info(f'{direction} finished with {expected_score} score')
            if expected_score is None:
                # solution has exceeded the best score and stopped
                continue

            if min_score is None or expected_score < min_score:
                min_score, min_actions, min_extra = expected_score, actions, extra

        return SolverResult(
            data=compose_actions(min_actions),
            expected_score=min_score,
            extra=min_extra)


# -------------------------- main ---------------------------------

def main():
    s = Path(utils.project_root() / 'tasks' / 'part-2-teleports' / 'prob-213.desc').read_text()

    args_options = (['squared', 'drill', 'teleport'],
                    ['squared', 'no-drill', 'teleport'],
                    ['squared', 'drill'],
                    ['squared', 'no-drill'])

    bestscore = None
    bestoption = None
    for arg in args_options:
        tweaker = TweakerSolver(arg)
        sol = tweaker.solve(s)
        print(sol.expected_score, 'time units')
        if bestscore is None or bestscore > sol.expected_score:
            bestscore, bestoption = sol.expected_score, arg
    print('\n: best option was ', bestoption, '\n')
    sol_path = Path(utils.project_root() / 'outputs' / 'prob-ttt-tweaker.sol')
    sol_path.write_text(sol.data)
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
