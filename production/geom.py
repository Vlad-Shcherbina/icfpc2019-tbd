from dataclasses import dataclass
from pathlib import Path

from production.data_formats import *
from production import utils


@dataclass
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


@dataclass
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


def main():
    #s = Path(utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01.desc').read_text()
    s = utils.get_problem_raw(11)
    t = Task.parse(s)
    bb = poly_bb(t.border)

    grid = [['#'] * (bb.x2 - bb.x1) for y in range(bb.y1, bb.y2)]

    for row in rasterize_poly(t.border):
        for x in range(row.x1, row.x2):
            assert grid[row.y - bb.y1][x - bb.x1] == '#'
            grid[row.y - bb.y1][x - bb.x1] = '.'

    for obstacle in t.obstacles:
        for row in rasterize_poly(obstacle):
            for x in range(row.x1, row.x2):
                assert grid[row.y - bb.y1][x - bb.x1] == '.'
                grid[row.y - bb.y1][x - bb.x1] = '#'

    for row in reversed(grid):
        print(' '.join(row))


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    from importlib.util import find_spec
    if find_spec('hintcheck'):
        import hintcheck
        hintcheck.hintcheck_all_functions()

    main()
