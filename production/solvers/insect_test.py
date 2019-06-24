from production import utils
from production.golden import validate
from production.solvers.insect import InsectSolver


def test_insect():
    s = (utils.project_root() / 'tasks' / 'part-0-mock' / 'prob-2003.desc').read_text()
    solver = InsectSolver([])
    result = solver.solve(s)
    print(result)
    vr = validate.run(s, result.data)
    print(vr)


if __name__ == '__main__':
    utils.testmod()
