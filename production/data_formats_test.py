from zipfile import ZipFile

from production.data_formats import Task, GridTask, Pt, Booster, Action, compose_actions
from production import utils


def test_parse_example_task():
    s = '(0,0),(10,0),(10,10),(0,10)#(0,0)#(4,2),(6,2),(6,7),(4,7);(5,8),(6,8),(6,9),(5,9)#B(0,1);B(1,1);F(0,2);F(1,2);L(0,3);X(0,9)'
    t = Task.parse(s)
    print(t)
    assert t.obstacles[1] == [Pt(5, 8), Pt(6, 8), Pt(6, 9), Pt(5, 9)]
    assert t.boosters[0] == Booster(code='B', pos=Pt(0, 1))


def test_parse_all_problems():
    for n in range(1, 300 + 1, 17):
        s = utils.get_problem_raw(n)
        t = Task.parse(s)


def test_compose():
    actions = [Action.WSAD(c) for c in 'WSAD'] + [
        Action.wait(),
        Action.turnCW(),
        Action.turnCCW(),
        Action.attach(1, -2),
        Action.wheels(),
        Action.drill(),
        ]
    assert compose_actions(actions) == 'WSADZEQB(1,-2)FL'


def test_grid_with_border():
    g1 = GridTask.from_problem(3)
    g2 = GridTask.from_problem(3, True)
    assert g1.width + 2 == g2.width
    assert g1.height + 2 == g2.height
    gr1, gr2 = g1.grid, g2.grid

    for y in range(g2.height):
        assert gr2[y][0] == gr2[y][g2.width - 1] == '#'

    for x in range(g2.width):
        assert gr2[0][x] == gr2[g2.height - 1][x] == '#'

    for y in range(g1.height):
        for x in range(g1.width):
            assert gr1[y][x] == gr2[y + 1][x + 1]


if __name__ == '__main__':
    utils.testmod()
