from typing import Optional
from collections import Counter
from production.data_formats import GridTask, Action, Pt, Booster
from production import geom


class InvalidActionException(Exception):
    pass


class Game:
    def __init__(self, task: GridTask):
        self.task = task
        self.grid = task.grid
        self.height = task.height
        self.width = task.width
        self.pos = task.start
        self.boosters = task.boosters
        self.turn = 0
        self.inventory = Counter()
        self.wheels_timer = 0
        self.drill_timer = 0

        self.manipulator = [Pt(1, -1), Pt(1, 0), Pt(1, 1), Pt(0, 0)]
        self.world_manipulator = []
        self.wrapped = set()
        self.unwrapped = {p for p in self.task.grid_iter() if self.grid[p.y][p.x] == '.'}
        self.update_wrapped()
        self.actions = []




    def update_wrapped(self):
        m = (p + self.pos for p in self.manipulator)
        self.world_manipulator = [p for p in m
            if 0 < p.x < self.width and 0 < p.y < self.height
            and geom.visible(self.grid, self.pos, p)
        ]
        self.wrapped.update(self.world_manipulator)
        self.unwrapped.difference_update(self.world_manipulator)


    def is_wrapped(self, p):
        return p in self.wrapped


    def finished(self) -> Optional[int]:
        if self.unwrapped:
            return None
        return self.turn


    def apply_action(self, action: Action):
        act = action.s

        if act in 'WSAD':
            np = self.pos + action.WSAD2DIR[act]
            if self.grid[np.y][np.x] != '.':
                raise InvalidActionException(f'Can\'t move into a tile: {self.grid[np.y][np.x]!r}')
            self.pos = np
            booster = [b for b in self.boosters if b.pos == np]
            if booster:
                [booster] = booster
                if booster.code in Booster.CODES:
                    self.inventory.update([booster.code])
                    self.boosters.remove(booster)
            self.update_wrapped()

        elif act == 'Q':
            self.manipulator = [p.rotated_ccw() for p in self.manipulator]
            self.update_wrapped()

        elif act == 'E':
            self.manipulator = [p.rotated_cw() for p in self.manipulator]
            self.update_wrapped()

        elif act in 'LF':
            if not self.inventory[act]:
                raise InvalidActionException('Out of {}s!'.format(Booster.description(act)))
            self.inventory.subtract(act)
            if act == 'L':
                self.drill_timer = 31 # not including current turn?
            else:
                self.wheels_timer = 51 # same

        else:
            raise InvalidActionException(f'Unknown action {action}')

        self.actions.append(action)
        self.turn += 1
        self.drill_timer = max(self.drill_timer - 1, 0)
        self.wheels_timer = max(self.wheels_timer - 1, 0)
