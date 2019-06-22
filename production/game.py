from typing import Optional
from collections import Counter
from production.data_formats import GridTask, Action, Pt, Booster
from production import geom


class InvalidActionException(Exception):
    pass


class Game:
    def __init__(self, task: GridTask):
        self.task = task
        self.grid = task.mutable_grid() # because drill
        self.height = task.height
        self.width = task.width
        self.pos = task.start
        self.boosters = task.boosters
        self.turn = 0
        self.inventory = Counter()
        self.wheels_timer = 0
        self.drill_timer = 0

        self.manipulator = [Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(1, -1)]
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
            for step in range(2 if self.wheels_timer else 1):
                np = self.pos + action.WSAD2DIR[act]
                target = self.grid[np.y][np.x]
                if target != '.':
                    if self.drill_timer and target == '#':
                        # "im not owned!  im not owned!!", the wall continues to insist
                        # as it slowly shrinks and transforms into a corn cob
                        self.grid[np.y][np.x] = '.'
                        self.unwrapped.add(np)
                    elif step:
                        # second step, OK to fail
                        break
                    else:
                        raise InvalidActionException(f'Can\'t move into a tile: {target!r}')

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
            # TODO: Should timers include current turn?
            if act == 'L':
                self.drill_timer = 31
            else:
                self.wheels_timer = 51

        elif act.startswith('B'):
            if not self.inventory['B']:
                raise InvalidActionException('Out of {}s!'.format(Booster.description('B')))
            self.inventory.subtract('B')
            pt = Pt.parse(act[1:])
            if pt in self.manipulator:
                raise InvalidActionException("manipulator already there")
            if not any(pt.manhattan_dist(m) == 1 for m in self.manipulator):
                raise InvalidActionException("manipulator should be adjacent to existing ones")
            self.manipulator.append(pt)
            self.update_wrapped()

        else:
            raise InvalidActionException(f'Unknown action {action}')

        self.actions.append(action)
        self.turn += 1
        self.drill_timer = max(self.drill_timer - 1, 0)
        self.wheels_timer = max(self.wheels_timer - 1, 0)
