from pathlib import Path

from production import utils
from production.data_formats import *
from production.solvers.greedy import solve
from production.golden import validate

def test_greedy_on_example():
    s = Path(utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01.desc').read_text()
    task = Task.parse(s)
    expected_score, actions = solve(task)

    res = validate.run(s, compose_actions(actions))
    print(res)
    assert res.time is not None

if __name__ == '__main__':
    utils.testmod()

