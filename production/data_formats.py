import dataclasses
from dataclasses import dataclass

from production import utils
from production.geom import Pt, Poly, List, parse_poly, poly_bb, rasterize_poly


@dataclass
class Booster:
    code: str  # char, actually
    pos: Pt

    @staticmethod
    def parse(s):
        code = s[0]
        assert code in list('BFLXRC')
        return Booster(code=code, pos=Pt.parse(s[1:]))


@dataclass
class Task:
    border: Poly
    start: Pt
    obstacles: List[Poly]
    boosters: List[Booster]

    @staticmethod
    def parse(s: str) -> 'Task':
        border, start, obstacles, boosters = s.split('#')
        if obstacles:
            obstacles = obstacles.split(';')
        else:
            obstacles = []
        if boosters:
            boosters = boosters.split(';')
        else:
            boosters = []

        return Task(
            border=parse_poly(border),
            start=Pt.parse(start),
            obstacles=list(map(parse_poly, obstacles)),
            boosters=list(map(Booster.parse, boosters)),
        )


@dataclass
class GridTask:
    start: Pt
    boosters: List[Booster]
    grid: List[List[str]]
    width: int
    height: int

    @staticmethod
    def from_problem(n, with_border=False):
        s = utils.get_problem_raw(n)
        return GridTask(Task.parse(s), with_border)


    def mutable_grid(self):
        return [[c for c in row] for row in self.grid]


    def grid_as_text(self):
        # TODO: add boosters and start
        return '\n'.join(' '.join(row) for row in self.grid)


    def grid_iter(self):
        'return indices in the grid'
        for y in range(self.height):
            for x in range(self.width):
                yield Pt(x, y)


    def __init__(self, task: Task, with_border=False):
        with_border = 1 if with_border else 0
        bb = poly_bb(task.border)
        self.width = width = bb.x2 - bb.x1 + 2 * with_border
        self.height = height = bb.y2 - bb.y1 + 2 * with_border
        offset = Pt(x=bb.x1 - with_border, y=bb.y1 - with_border)

        self.start = task.start - offset
        self.boosters=[dataclasses.replace(it, pos=it.pos - offset) for it in task.boosters]

        # todo C++ grid

        grid = [['#'] * width for _ in range(height)]

        # todo: with_border implies impassable border?

        def render(poly, c):
            for row in rasterize_poly(poly):
                for x in range(row.x1 - offset.x, row.x2 - offset.x):
                    assert grid[row.y - offset.y][x] != c
                    grid[row.y - offset.y][x] = c

        render(task.border, '.')

        for obstacle in task.obstacles:
            render(obstacle, '#')

        # safety
        self.grid = tuple(''.join(row) for row in grid)


@dataclass
class Action:
    s : str

    def __str__(self):
        return self.s


    @staticmethod
    def WSAD(c: str):
        'Other movement->action methods shall be added as useful move encoding is determined'
        assert c in 'WASD'
        return Action(c)

    @staticmethod
    def from_key(c: str):
        'Returns None on failure, for your convenience'
        if c in 'WSADQEFL':
            return Action(c)

    @staticmethod
    def wait():
        return Action('Z')


    @staticmethod
    def turnCW():
        return Action('E')


    @staticmethod
    def turnCCW():
        return Action('Q')


    @staticmethod
    def attach(dx, dy):
        return Action(f'B({dx},{dy})')


    @staticmethod
    def wheels():
        return Action('F')


    @staticmethod
    def drill():
        return Action('L')

Action.DIRS = {
    Pt(0, 1): Action.WSAD('W'),
    Pt(0, -1): Action.WSAD('S'),
    Pt(-1, 0): Action.WSAD('A'),
    Pt(1, 0): Action.WSAD('D'),
}

Action.WSAD2DIR = dict((v.s, k) for k, v in Action.DIRS.items())


def compose_actions(lst: List[Action]):
    return ''.join(map(str, lst))
