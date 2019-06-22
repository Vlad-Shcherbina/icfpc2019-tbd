import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import List
import re


'''
IMPORTANT: we write Pt(x, y), but grid[y][x] for various grids. Such is life.

At some point we'll write a grid class in C++, indexed with Pt's, which would mostly eliminate the confusion.

'''

@dataclass(frozen=True)
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

    def rotated_cw(self):
        return Pt(x=self.y, y=-self.x)


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



@dataclass(frozen=True)
class Rect:
    x1: int
    y1: int
    x2: int
    y2: int


def poly_bb(poly: Poly) -> Rect:
    x1 = min(pt.x for pt in poly)
    y1 = min(pt.y for pt in poly)
    x2 = max(pt.x for pt in poly)
    y2 = max(pt.y for pt in poly)
    return Rect(x1=x1, y1=y1, x2=x2, y2=y2)


@dataclass(frozen=True)
class Row:
    y: int
    x1: int
    x2: int


def rasterize_poly(poly: Poly) -> List[Row]:
    bb = poly_bb(poly)

    row_ends = [[] for y in range(bb.y2 - bb.y1)]

    for pt1, pt2 in zip(poly, poly[1:] + poly[:1]):
        if pt1.y == pt2.y:
            continue
        assert pt1.x == pt2.x
        if pt1.y < pt2.y:
            for y in range(pt1.y, pt2.y):
                row_ends[y - bb.y1].append((pt1.x, -1))
        elif pt2.y < pt1.y:
            for y in range(pt2.y, pt1.y):
                row_ends[y - bb.y1].append((pt1.x, 1))
        else:
            assert False

    result = []
    for y, t in enumerate(row_ends, start=bb.y1):
        assert len(t) % 2 == 0
        t.sort()
        for start, end in zip(t[::2], t[1::2]):
            assert start[1] == 1
            assert end[1] == -1
            x1 = start[0]
            x2 = end[0]
            assert x1 < x2
            result.append(Row(y=y, x1=x1, x2=x2))

    return result


def visible(grid, p1: Pt, p2: Pt):
    dist = (p2 - p1)
    divider = (abs(dist.x) + abs(dist.y)) * 2 + 1
    move = (dist.x / divider, dist.y / divider)

    current = (p1.x + 0.5, p1.y + 0.5)

    def to_int(p):
        return Pt(int(p[0]), int(p[1]))

    while True:
        current = (current[0] + move[0], current[1] + move[1])
        p = to_int(current)
        if grid[p.y][p.x] == '#':
            return False
        if p == p2:
            return True
    return True


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    from importlib.util import find_spec
    if find_spec('hintcheck'):
        import hintcheck
        hintcheck.hintcheck_all_functions()
