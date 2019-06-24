from typing import Optional
from collections import Counter
from production.data_formats import GridTask, Action, Pt, Pt_parse, CharGrid, ByteGrid, Booster, enumerate_grid
from production import geom
from production.cpp_grid.cpp_grid_ext import manipulators_will_wrap
from copy import copy


class InvalidActionException(Exception):
    pass


class Bot:
    def __init__(self, pos: Pt):
        self.pos = pos
        self.manipulator = [Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(1, -1)]
        self.int_direction = 0 # for bookkeeping purposes
        self.wheels_timer = 0
        self.drill_timer = 0
        self.actions = []
        self.last_delta = []


    def rotate(self, direction: int):
        if direction > 0:
            self.manipulator = [p.rotated_cw() for p in self.manipulator]
        else:
            self.manipulator = [p.rotated_ccw() for p in self.manipulator]

        self.int_direction = (self.int_direction + direction) & 3


class Game:
    def __init__(self, task: GridTask):
        self.task = task
        self.grid = task.mutable_grid() # because drill
        self.height = task.height
        self.width = task.width
        self.bots = [Bot(task.start)]

        self.pending_boosters = []
        self.inventory = Counter()
        self.boosters = [b for b in task.boosters if b.code != 'X']
        self.clone_spawn = [b.pos for b in task.boosters if b.code == 'X']
        self.teleport_spots = []
        self.turn = 0

        self._wrapped = ByteGrid(self.grid.height, self.grid.width)
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[Pt(x, y)] != '.':
                    self._wrapped[Pt(x, y)] = 1

        self._remaining_unwrapped = sum(1 for _, c in self.enumerate_grid() if c == '.')

        self.update_wrapped()

    def map_contains_booster(self, code):
        return any(code == b.code for b in self.boosters)

    @property
    def remaining_unwrapped(self):
        return self._remaining_unwrapped


    def in_bounds(self, p: Pt):
        return self.grid.in_bounds(p)


    def is_passable(self, p: Pt):
        return self.grid[p] == '.'


    def enumerate_grid(self):
        return enumerate_grid(self.grid)


    def size(self) -> Pt:
        return Pt(self.width, self.height)


    def update_wrapped(self):
        for bot in self.bots:
            delta = manipulators_will_wrap(self.grid, self._wrapped, bot.pos, bot.manipulator)
            num_changed = self._wrapped.update_values(delta, 1)
            assert num_changed == len(delta)
            self._remaining_unwrapped -= num_changed
            bot.last_delta = delta


    def is_wrapped(self, p):
        return bool(self._wrapped[p])


    def finished(self) -> Optional[int]:
        if self._remaining_unwrapped:
            return
        return self.turn


    def apply_action(self, action: Action, bot_index: int=0):
        if self.finished():
            raise InvalidActionException(f'Game already finished! bot {bot_index} tried to {action}')

        # you should always call the zero's bot action explicitely,
        # even if it's Z, since he counts turns

        act = action.s
        bot = self.bots[bot_index]

        def get_booster(x):
            b, t, i = x
            if self.turn > t + 2 or self.turn == t + 1 and i >= bot_index:
                self.inventory.update([b])
                return False
            return True

        self.pending_boosters = [x for x in self.pending_boosters if get_booster(x)]


        if act in 'WSAD':
            for step in range(2 if bot.wheels_timer else 1):

                np = bot.pos + action.WSAD2DIR[act]
                if not self.in_bounds(np):
                    raise InvalidActionException('Can\'t move out of map boundary')

                target = self.grid[np]
                if target != '.':
                    if bot.drill_timer and target == '#':
                        # "im not owned!  im not owned!!", the wall continues to insist
                        # as it slowly shrinks and transforms into a corn cob
                        self.grid[np] = '.'
                        assert self._wrapped[np]
                        self._wrapped[np] = 0
                        self._remaining_unwrapped += 1
                    elif step:
                        # second step, OK to fail
                        break
                    else:
                        raise InvalidActionException(f'Can\'t move into a tile: {target!r}')
                bot.pos = np
                booster = [b for b in self.boosters if b.pos == bot.pos]
                if booster:
                    [booster] = booster
                    if booster.code in Booster.CODES:
                        self.pending_boosters.append((booster.code, self.turn, bot_index))
                        # self.inventory.update([booster.code])
                        self.boosters.remove(booster)
                self.update_wrapped()

        elif act == 'Q':
            bot.rotate(-1)

        elif act == 'E':
            bot.rotate(1)

        elif act == 'Z':
            pass

        elif act in 'LFR':
            if not self.inventory[act]:
                raise InvalidActionException('Out of {}s!'.format(Booster.description(act)))
            self.inventory.subtract(act)
            if act == 'L':
                bot.drill_timer = max(31, bot.drill_timer + 30)
            elif act == 'F':
                bot.wheels_timer = max(51, bot.wheels_timer + 50)
            else:
                self.teleport_spots.append(bot.pos)


        elif act.startswith('B'):
            if not self.inventory['B']:
                raise InvalidActionException('Out of {}s!'.format(Booster.description('B')))
            pt = Pt_parse(act[1:])
            if pt in bot.manipulator:
                raise InvalidActionException("manipulator already there")
            if not any(pt.manhattan_dist(m) == 1 for m in bot.manipulator):
                raise InvalidActionException("manipulator should be adjacent to existing ones")
            bot.manipulator.append(pt)
            self.inventory.subtract('B')


        elif act.startswith('T'):
            pt = Pt_parse(act[1:])
            if pt not in self.teleport_spots:
                raise InvalidActionException("no teleport at destination")
            bot.pos = pt


        elif act == 'C':
            if not self.inventory['C']:
                raise InvalidActionException('Out of {}s!'.format(Booster.description('C')))
            if not bot.pos in self.clone_spawn:
                raise InvalidActionException('No clone spawn in current position')
            self.inventory.subtract('C')
            self.bots.append(Bot(bot.pos))


        else:
            raise InvalidActionException(f'Unsupported action {action}')


        self.update_wrapped()
        bot.actions.append(action)
        if bot_index == 0:
            self.turn += 1
        for bot in self.bots:
            bot.drill_timer = max(bot.drill_timer - 1, 0)
            bot.wheels_timer = max(bot.wheels_timer - 1, 0)


    def get_actions(self):
        return [b.actions for b in self.bots]


class BacktrackingGame:
    'An ethereal version of Game that only supports movement actions but with efficient backtracking'
    def __init__(self, game: Game, bot: Bot):
        self.game = game

        self.bot = copy(bot)
        self._wrapped = game._wrapped.copy() # better copy one time than try to ensure full rollback
        self.remaining_unwrapped = game.remaining_unwrapped
        self.turn = game.turn

        # A super-clever way to provide an immutable interface on top of mutable implementation with
        # zero overhead in backtracking usecase.
        self._child : BacktrackingGame = None
        self._revert_action = None
        self._reverted = False


    def _create_child(self, bot, revert):
        # bypass __init__
        child = self._child = BacktrackingGame.__new__(BacktrackingGame)

        child.game = self.game
        child.bot = bot
        child._wrapped = self._wrapped
        child.remaining_unwrapped = self.remaining_unwrapped
        child.turn = self.turn + 1

        child._child = None
        child._revert_action = revert
        child._reverted = False

        return child


    def _activate(self):
        assert not self._reverted
        if self._child:
            self._child._revert()
            self._child = None


    def _revert(self):
        self._activate() # will revert children
        self._revert_action()
        self._reverted = True


    def apply_action(self, action: Action):
        self._activate()

        act = action.s
        bot = copy(self.bot)

        if act in 'WSAD':
            revert_infos = []
            for step in range(2 if bot.wheels_timer else 1):
                np = bot.pos + action.WSAD2DIR[act]
                if not self.in_bounds(np):
                    raise InvalidActionException('Can\'t move out of map boundary')

                target = self.game.grid[np]
                if target != '.': # don't support drilling
                    if not step:
                        raise InvalidActionException(f'Can\'t move into a tile: {target!r}')
                    else:
                        break

                bot.pos = np
                revert_infos.append(self.update_wrapped())
            revert_infos.reverse()
            return self._create_child(bot, lambda: [self.revert_update_wrapped(r) for r in revert_infos])

        elif act in 'QE':
            direction = -1 if act == 'Q' else 1
            bot.rotate(direction)
            revert_info = self.update_wrapped()
            return self._create_child(bot, lambda: self.revert_update_wrapped(revert_info))

        else:
            raise InvalidActionException(f'Unsupported action {action}')

        # don't update bot timeouts and stuff

    def in_bounds(self, p: Pt):
        return self.game.grid.in_bounds(p)


    def is_passable(self, p: Pt):
        return self.game.grid[p] == '.'


    def enumerate_grid(self):
        return enumerate_grid(self.game.grid)


    def size(self) -> Pt:
        return Pt(self.game.width, self.game.height)


    def update_wrapped(self):
        delta = manipulators_will_wrap(self.game.grid, self._wrapped, self.bot.pos, self.bot.manipulator)
        num_changed = self._wrapped.update_values(delta, 1)
        assert num_changed == len(delta)
        self.remaining_unwrapped -= num_changed
        return delta


    def revert_update_wrapped(self, delta):
        self._wrapped.update_values(delta, 0)
        self.remaining_unwrapped += len(delta)


    def is_wrapped(self, p):
        return bool(self._wrapped[p])

