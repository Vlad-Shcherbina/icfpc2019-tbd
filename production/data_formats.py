from dataclasses import dataclass
from typing import List
import re


@dataclass
class Pt:
    x: int
    y: int

    @staticmethod
    def parse(s):
        m = re.match(r'\((\d+),(\d+)\)$', s)
        assert m, s
        return Pt(x=int(m.group(1)), y=int(m.group(2)))

    def __add__(self, other):
        return Pt(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other):
        return Pt(x=self.x - other.x, y=self.y - other.y)

    def rotated_ccw(self):
        return Pt(x=-self.y, y=self.x)


Poly = List[Pt]

def parse_poly(s) -> Poly:
    poly = []
    s += ','
    i = 0
    r = re.compile(r'\((\d+),(\d+)\),')
    while i < len(s):
        m = r.match(s, pos=i)
        assert m, (s, i)
        poly.append(Pt(x=int(m.group(1)), y=int(m.group(2))))
        i = m.end()
    return poly


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
class Action:
    s : str

    def __repr__(self):
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