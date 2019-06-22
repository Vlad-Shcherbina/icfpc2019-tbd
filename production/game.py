from typing import Optional

from production.data_formats import GridTask, Action, Pt
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
        self.manipulator = [Pt(1, -1), Pt(1, 0), Pt(1, 1), Pt(0, 0)]
        self.world_manipulator = []
        self.wrapped = set()
        self.unwrapped = {p for p in self.task.grid_iter() if self.grid[p.y][p.x] != '#'}
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
        if action.s in 'WSAD':
            np = self.pos + action.WSAD2DIR[action.s]
            if self.grid[np.y][np.x] != '.':
                raise InvalidActionException(f'Can\'t move into a tile: {self.grid[np.y][np.x]!r}')
            self.pos = np
            self.update_wrapped()
        elif action.s == 'Q':
            self.manipulator = [p.rotated_ccw() for p in self.manipulator]
            self.update_wrapped()
        elif action.s == 'E':
            self.manipulator = [p.rotated_cw() for p in self.manipulator]
            self.update_wrapped()
        else:
            raise InvalidActionException(f'Unknown action {action}')
        self.actions.append(action)
        self.turn += 1
