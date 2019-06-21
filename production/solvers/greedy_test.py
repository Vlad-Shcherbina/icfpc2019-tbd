from pathlib import Path

from production import utils
from production.data_formats import *
from production.solvers.greedy import solve


def test_greedy_on_example():
    s = Path(utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01.desc').read_text()
    task = Task.parse(s)
    sol = solve(task)
    print(sol)
    # TODO: validate
