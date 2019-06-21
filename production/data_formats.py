import dataclasses
from dataclasses import dataclass

from production import utils
from production.geom import Pt, Poly, List, parse_poly, poly_bb, rasterize_poly


@dataclass
class Booster:
    code: str  # 'B', 'F', 'L', 'X'
    pos: Pt

    @staticmethod
    def parse(s):
        code = s[0]
        assert code in list('BFLX')
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

    @staticmethod
    def from_problem(n):
        s = utils.get_problem_raw(n)
        return GridTask(Task.parse(s))


    def __init__(self, task: Task, extra_border=False):
        extra_border = 1 if extra_border else 0
        bb = poly_bb(task.border)
        width = bb.x2 - bb.x1 + 2 * extra_border
        height = bb.y2 - bb.y1 + 2 * extra_border
        offset = Pt(x=bb.x1 - extra_border, y=bb.y1 - extra_border)

        self.start = task.start - offset
        self.boosters=[dataclasses.replace(it, pos=it.pos - offset) for it in task.boosters]

        # todo C++ grid

        grid = [['#'] * width for _ in range(height)]

        # todo: extra_border implies impassable border?

        def render(poly, c):
            for row in rasterize_poly(poly):
                for x in range(row.x1 - offset.x + extra_border, row.x2 - offset.x + extra_border):
                    assert grid[row.y - offset.y][x] != c
                    grid[row.y - offset.y][x] = c

        render(task.border, '.')

        for obstacle in task.obstacles:
            render(obstacle, '#')

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


def compose_actions(lst: List[Action]):
    return ''.join(map(str, lst))
