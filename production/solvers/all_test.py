import pytest

from production import utils
from production.data_formats import *
from production.golden import validate
from production.solvers import interface

from production.solvers.all import ALL_SOLVERS

'''Smoke-test basic functionality'''


@pytest.mark.parametrize('name, Solver', ALL_SOLVERS.items())
def test_example1(name, Solver):
    s = utils.get_problem_raw(1)
    result = Solver([]).solve(s)
    if isinstance(result.data, interface.Pass):
        pytest.skip(f'solver {Solver} passed')
    vres = validate.run(s, result.data)
    print(vres)
    assert vres.time == result.expected_score


if __name__ == '__main__':
    utils.testmod()

