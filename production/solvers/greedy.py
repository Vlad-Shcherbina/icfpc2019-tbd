import logging
logger = logging.getLogger(__name__)
from pathlib import Path

from production import utils
from production.data_formats import *
from production.geom import poly_bb, rasterize_poly
from production.solvers.interface import *


def solve(task: Task) -> List[Action]:
    task = GridTask(task, with_border=True)

    grid = task.mutable_grid()
    worker_pos = task.start
    manips = [Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(1, -1)]
    #logger.info(worker_pos)

    cells_to_wrap = sum(row.count('.') for row in grid)
    solution = []
    while True:
        for m in manips:
            p = worker_pos + m
            if grid[p.y][p.x] == '.':
                grid[p.y][p.x] = '+'
                cells_to_wrap -= 1
        # for row in reversed(grid):
        #     print(' '.join(row))
        # print(cells_to_wrap)
        if cells_to_wrap == 0:
            break

        prev = {worker_pos: None}
        frontier = [worker_pos]
        while frontier:
            dst = None
            for p in frontier:
                for m in manips:
                    q = p + m
                    if grid[q.y][q.x] == '.':
                        dst = p
            if dst is not None:
                break

            new_frontier = []
            for p in frontier:
                for d in Action.DIRS.keys():
                    p2 = p + d
                    if p2 not in prev and grid[p2.y][p2.x] != '#':
                        prev[p2] = p
                        new_frontier.append(p2)
            frontier = new_frontier

        assert dst is not None

        path = []
        p = dst
        while p != worker_pos:
            d = p - prev[p]
            path.append(Action.DIRS[d])
            p = prev[p]
            assert p is not None
        path.reverse()
        # print(path)
        solution += path

        worker_pos = dst

    return solution


class GreedySolver(Solver):
    def __init__(self, args: List[str]):
        [] = args

    def scent(self) -> str:
        return 'greedy 1'

    def solve(self, task: str) -> SolverResult:
        task = Task.parse(task)
        sol = solve(task)
        return SolverResult(
            data=compose_actions(sol),
            expected_score=len(sol))


def main():
    s = Path(utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01.desc').read_text()
    task = Task.parse(s)
    sol = solve(task)
    sol = compose_actions(sol)
    print(sol)
    print(len(sol), 'time units')
    sol_path = Path(utils.project_root() / 'outputs' / 'example-01-greedy.sol')
    sol_path.write_text(sol)
    print('result saved to', sol_path)


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
