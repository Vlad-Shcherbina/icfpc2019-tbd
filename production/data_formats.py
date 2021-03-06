import dataclasses
import re
from dataclasses import dataclass
from typing import ClassVar, Dict, Tuple
from copy import copy

from production import utils
from production.geom import Pt, Pt_parse, CharGrid, ByteGrid, IntGrid
from production.geom import Poly, List, parse_poly, poly_bb, rasterize_poly, enumerate_grid

@dataclass
class Puzzle:
    block: int
    epoch: int
    size: int
    vertices: Dict[str, int]
    extensions: int
    wheels: int
    drills: int
    teleports: int
    clones: int
    spawnPoints: int
    include: List[Pt]
    omit:    List[Pt]

    @property
    def min_vertices(self):
        return self.vertices['min']

    @property
    def max_vertices(self):
        return self.vertices['max']

    def __str__(self):
        def render(x):
            out = []
            cx = 0
            cy = self.size-1
            yoff = (self.size ** 2) - self.size
            while cy >= 0:
                while cx < self.size:
                    off = yoff + cx
                    cx = cx + 1
                    out.append(x[off])
                cy = cy - 1
                cx = 0
                yoff = yoff - self.size
                out.append('\n')
            return ''.join(out)
        map = ['.' for i in range((self.size) ** 2)]
        for p in self.include:
            map[_o(self.size, p.x, p.y)] = 'I'
        for p in self.omit:
            map[_o(self.size, p.x, p.y)] = 'O'
        return render(map)

    @staticmethod
    def parse(x: str) -> 'Puzzle':
        s  = x.split('#')
        s0 = s[0].split(',')
        return Puzzle(
            block=int(s0[0]),
            epoch=int(s0[1]),
            size=int(s0[2]),
            vertices={'min': int(s0[3]), 'max': int(s0[4])},
            extensions=int(s0[5]),
            wheels=int(s0[6]),
            drills=int(s0[7]),
            teleports=int(s0[8]),
            clones=int(s0[9]),
            spawnPoints=int(s0[10]),
            include=_toListOfPoints(s[1]),
            omit=_toListOfPoints(s[2])
        )
    @staticmethod
    def o(s, x, y):
       return y*s + x


def _toListOfPoints(x: str) -> List[Pt]:
    y = []
    xx = x.split('),(')
    xx[0] = xx[0].strip('(')
    xx[-1] = xx[-1].strip(')')
    # yeah, yeah, I know
    for v in xx:
        z = v.split(',')
        y.append(Pt(int(z[0]), int(z[1])))
    return y


@dataclass
class Booster:
    code: str  # char, actually
    pos: Pt

    PICKABLE: ClassVar[str] = 'BFLRC'
    CODES: ClassVar[str] = PICKABLE + 'X'

    def __str__(self):
        return f'{self.code}{self.pos}'

    @staticmethod
    def parse(s):
        code = s[0]
        assert code in Booster.CODES
        return Booster(code=code, pos=Pt_parse(s[1:]))

    def description(s):
        'Black magic: can be called both on strings and on instances'
        if isinstance(s, Booster):
            s = s.code
        return {
            'B': 'extension',
            'F': 'wheel',
            'L': 'drill',
            'C': 'clone',
            'R': 'teleport'
        }[s]


@dataclass
class Task:
    border: Poly
    start: Pt
    obstacles: List[Poly]
    boosters: List[Booster]

    def __str__(self):
        border = ','.join(map(str, self.border))
        obstacles = []
        for obstacle in self.obstacles:
            obstacles.append(','.join(map(str, obstacle)))
        obstacles = ';'.join(obstacles)
        boosters = ';'.join(map(str, self.boosters))
        return f'{border}#{self.start}#{obstacles}#{boosters}'

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
            start=Pt_parse(start),
            obstacles=list(map(parse_poly, obstacles)),
            boosters=list(map(Booster.parse, boosters)),
        )


@dataclass
class GridTask:
    start: Pt
    boosters: List[Booster]
    grid: CharGrid

    @property
    def width(self) -> int:
        return self.grid.width

    @property
    def height(self) -> int:
        return self.grid.height

    @staticmethod
    def from_problem(n):
        s = utils.get_problem_raw(n)
        return GridTask(Task.parse(s))


    def mutable_grid(self):
        return self.grid.copy()


    def grid_as_text(self):
        # TODO: add boosters and start
        return self.grid.grid_as_text()


    def __init__(self, task: Task):
        # do not do bounding box optimization
        self.start = task.start
        self.boosters = copy(task.boosters)

        # todo C++ grid

        bb = poly_bb(task.border)
        grid = self.grid = CharGrid(bb.y2, bb.x2, '#')

        def render(poly, c):
            for row in rasterize_poly(poly):
                for x in range(row.x1, row.x2):
                    assert grid[Pt(x, row.y)] != c
                    grid[Pt(x, row.y)] = c

        render(task.border, '.')

        for obstacle in task.obstacles:
            render(obstacle, '#')

        # TODO: make grid immutable as before?


param_action_re = re.compile(r'[B|T]\(-?\d+,-?\d+\)') # B(-1,2) or T(3,5)

@dataclass
class Action:
    s : str

    SIMPLE: ClassVar[str] = 'WSADZQEFLRC' # 'X' is not a pickable booster
    PARAM: ClassVar[str] = 'BT' # 'X' is not a pickable booster

    def __str__(self):
        return self.s


    @staticmethod
    def WSAD(c: str):
        'Other movement->action methods shall be added as useful move encoding is determined'
        assert c in 'WASD'
        return Action(c)

    @staticmethod
    def simple(c: str):
        'Returns None on failure, for your convenience'
        if c in Action.SIMPLE:
            return Action(c)

    @staticmethod
    def parameterized(c: str):
        'Returns None on failure'
        if param_action_re.match(c):
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

    @staticmethod
    def reset():
        return Action('R')

    @staticmethod
    def teleport(x, y):
        return Action(f'T({x},{y})')

    @staticmethod
    def clone():
        return Action('C')


    @staticmethod
    def parse(s: str) -> List['Action']:
        actions = []
        i = 0
        while i < len(s):
            if s[i] in Action.SIMPLE:
                actions.append(Action.simple(s[i]))
                i += 1
            elif s[i] in Action.PARAM:
                m = param_action_re.match(s, i)
                assert m, s[i:]
                actions.append(Action.parameterized(m[0]))
                i = m.end()
            else:
                assert False, s[i:]
        return actions


Action.DIRS = {
    Pt(0, 1): Action.WSAD('W'),
    Pt(0, -1): Action.WSAD('S'),
    Pt(-1, 0): Action.WSAD('A'),
    Pt(1, 0): Action.WSAD('D'),
}

Action.WSAD2DIR = dict((v.s, k) for k, v in Action.DIRS.items())


def compose_actions(lst: List[List[Action]]):
    return '#'.join(''.join(map(str, x)) for x in lst)

