import logging
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')
logger = logging.getLogger(__name__)

from production import utils
from production.data_formats import *
from production import geom
from production.golden import validate
import random


def solve(puzzle: Puzzle) -> Task:
    include = set(puzzle.include)
    omit = set(puzzle.omit)

    cells = {Pt(x, y) for x in range(puzzle.size) for y in range(puzzle.size)}
    for pt in puzzle.include:
        assert pt in cells, pt

    while omit & cells:
        front = list(omit & cells)
        if len(front) % 10 == 0:
            logging.info(f'{len(front)} more cells to omit..')
        visited = set(front)
        prev = dict.fromkeys(front, None)
        z = None
        while front and z is None:
            front2 = []
            for pt in front:
                for d in Action.DIRS:
                    pt2 = pt + d
                    if pt2 in visited or pt2 in include:
                        continue
                    visited.add(pt2)
                    front2.append(pt2)
                    prev[pt2] = pt
                    if pt2 not in cells:
                        z = pt2
            front = front2
        assert z is not None
        z = prev[z]
        while z is not None:
            assert z in cells
            cells.remove(z)
            z = prev[z]

    assert include.issubset(cells)
    assert not (omit & cells)

    poly = geom.trace_poly(cells)

    while len(poly) < puzzle.min_vertices:
        num_steps = (puzzle.min_vertices - len(poly) - 1) // 4 + 1
        for _ in range(num_steps):
            cx = list(cells)
            while True:
                cell = random.choice(cx)
                n = 0
                for d in Action.DIRS:
                    if cell + d in cells:
                        n += 1
                if n == 3:
                    break
            cells.remove(cell)
        poly = geom.trace_poly(cells)

    assert len(poly) <= puzzle.max_vertices, (len(poly), puzzle.max_vertices)

    cells = list(cells)
    random.shuffle(cells)

    boosters = []
    for _ in range(puzzle.extensions):
        boosters.append(Booster('B', cells.pop(-1)))
    for _ in range(puzzle.wheels):
        boosters.append(Booster('F', cells.pop(-1)))
    for _ in range(puzzle.drills):
        boosters.append(Booster('L', cells.pop(-1)))
    for _ in range(puzzle.clones):
        boosters.append(Booster('C', cells.pop(-1)))
    for _ in range(puzzle.teleports):
        boosters.append(Booster('R', cells.pop(-1)))
    for _ in range(puzzle.spawnPoints):
        boosters.append(Booster('X', cells.pop(-1)))

    task = Task(border=poly, start=cells.pop(-1), obstacles=[], boosters=boosters)

    return task


def main():
    puzzle = utils.project_root() / 'tasks' / 'chain-puzzle-examples' / 'puzzle.cond'
    puzzle_str = puzzle.read_text()
    puzzle = Puzzle.parse(puzzle_str)
    print(repr(puzzle))
    # return
    print('solving...')
    task = solve(puzzle)

    (utils.project_root() / 'outputs' / 'my_task.desc').write_text(str(task))

    result = validate.puz(puzzle_str, str(task))
    print(result)


if __name__ == '__main__':
    main()
