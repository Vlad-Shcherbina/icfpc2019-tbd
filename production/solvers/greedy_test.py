from pathlib import Path

from production import utils
from production.data_formats import *
from production.solvers.greedy import solve
from production.golden import validate

def test_greedy_with_extensions():
    s = utils.get_problem_raw(2)
    task = Task.parse(s)
    expected_score, actions, extra = solve(task)

    assert extra['final_manipulators'] > 4

    res = validate.run(s, compose_actions(actions))
    print(res)
    assert res.time is not None
    assert res.time == expected_score


if __name__ == '__main__':
    utils.testmod()

