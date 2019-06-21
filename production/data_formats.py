from dataclasses import dataclass
from typing import List
import re


@dataclass
class Point:
    x: int
    y: int

    @staticmethod
    def parse(s):
        m = re.match(r'\((\d+),(\d+)\)$', s)
        assert m, s
        return Point(x=int(m.group(1)), y=int(m.group(2)))


Poly = List[Point]

def parse_poly(s) -> Poly:
    poly = []
    s += ','
    i = 0
    r = re.compile(r'\((\d+),(\d+)\),')
    while i < len(s):
        m = r.match(s, pos=i)
        assert m, (s, i)
        poly.append(Point(x=int(m.group(1)), y=int(m.group(2))))
        i = m.end()
    return poly


@dataclass
class Booster:
    code: str  # 'B', 'F', 'L', 'X'
    pos: Point

    @staticmethod
    def parse(s):
        code = s[0]
        assert code in list('BFLX')
        return Booster(code=code, pos=Point.parse(s[1:]))


@dataclass
class Task:
    border: Poly
    start: Point
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
            start=Point.parse(start),
            obstacles=list(map(parse_poly, obstacles)),
            boosters=list(map(Booster.parse, boosters)),
        )
