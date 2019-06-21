from zipfile import ZipFile

from production.data_formats import Task, Point, Booster, Action, compose_actions
from production import utils


def test_parse_example_task():
    s = '(0,0),(10,0),(10,10),(0,10)#(0,0)#(4,2),(6,2),(6,7),(4,7);(5,8),(6,8),(6,9),(5,9)#B(0,1);B(1,1);F(0,2);F(1,2);L(0,3);X(0,9)'
    t = Task.parse(s)
    print(t)
    assert t.obstacles[1] == [Point(5, 8), Point(6, 8), Point(6, 9), Point(5, 9)]
    assert t.boosters[0] == Booster(code='B', pos=Point(0, 1))


def test_parse_all_problems():
    with ZipFile(utils.project_root() / 'tasks' / 'part-1-initial.zip') as z:
        for filename in z.namelist():
            if filename == 'part-1-legend.txt':
                continue
            assert filename.endswith('.desc'), filename
            print(filename)
            with z.open(filename, 'r') as fin:
                s = fin.read().decode()
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

if __name__ == '__main__':
    utils.testmod()
