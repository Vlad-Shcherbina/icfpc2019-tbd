import pytest

from production import utils
from production.data_formats import *
from production.golden import validate

from production.solvers.all import ALL_SOLVERS

'''Smoke-test basic functionality'''


@pytest.mark.parametrize('name, Solver', ALL_SOLVERS.items())
def test_example1(name, Solver):
    if Solver.__name__ == 'InsectSolver':
        pytest.skip('whatever')

    s = utils.get_problem_raw(1)
    result = Solver([]).solve(s)
    vres = validate.run(s, result.data)
    print(vres)
    assert vres.time == result.expected_score


if __name__ == '__main__':
    utils.testmod()

