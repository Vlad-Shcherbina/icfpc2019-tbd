from zipfile import ZipFile

from production.data_formats import Task, GridTask, Pt, Booster, Action, compose_actions, Puzzle
from production import utils


def test_parse_example_task():
    s = '(0,0),(10,0),(10,10),(0,10)#(0,0)#(4,2),(6,2),(6,7),(4,7);(5,8),(6,8),(6,9),(5,9)#B(0,1);B(1,1);F(0,2);F(1,2);L(0,3);C(0,9);R(5,5);X(0,10)'
    t = Task.parse(s)
    print(t)
    assert t.obstacles[1] == [Pt(5, 8), Pt(6, 8), Pt(6, 9), Pt(5, 9)]
    assert t.boosters[0] == Booster(code='B', pos=Pt(0, 1))


def test_parse_and_serialize_all_problems():
    for n in range(1, 300 + 1, 17):
        s = utils.get_problem_raw(n)
        t = Task.parse(s)
        assert s == str(t)


def test_compose():
    actions = [[Action.WSAD(c) for c in 'WSAD'] + [
        Action.wait(),
        Action.turnCW(),
        Action.turnCCW(),
        Action.attach(1, -2),
        Action.wheels(),
        Action.drill(),
        ]]
    assert compose_actions(actions) == 'WSADZEQB(1,-2)FL'
    actions = [
        [Action.WSAD(c) for c in 'WSAD'] + [
            Action.wait(),
            Action.turnCW(),
            Action.turnCCW()],
        [Action.attach(1, -2),
            Action.wheels(),
            Action.drill(),
        ]]
    assert compose_actions(actions) == 'WSADZEQ#B(1,-2)FL'


# def test_grid_with_border():
#     g1 = GridTask.from_problem(3)
#     g2 = GridTask.from_problem(3, True)
#     assert g1.width + 2 == g2.width
#     assert g1.height + 2 == g2.height
#     gr1, gr2 = g1.grid, g2.grid

#     for y in range(g2.height):
#         assert gr2[y][0] == gr2[y][g2.width - 1] == 'H'

#     for x in range(g2.width):
#         assert gr2[0][x] == gr2[g2.height - 1][x] == 'H'

#     for y in range(g1.height):
#         for x in range(g1.width):
#             assert gr1[y][x] == gr2[y + 1][x + 1]


def test_booster_description():
    assert Booster.description('F') == 'wheel'
    assert Booster('F', Pt(0, 0)).description() == 'wheel'


def test_puzzle():
    puz = "1,1,200,400,1200,6,10,5,1,3,4#(117,146),(36,132),(119,69),(173,139),(45,26),(169,84),(135,74),(89,44),(111,98),(73,125),(127,140),(95,74),(36,20),(180,76),(47,28),(71,92),(177,138),(52,179),(122,83),(173,137),(179,102),(24,139),(91,95),(91,162),(79,116),(187,115),(127,123),(116,68),(60,168),(56,180),(37,19),(12,135),(120,90),(39,19),(59,131),(105,48),(29,131),(38,36),(31,135),(118,119),(73,160),(57,85),(100,77),(87,74),(89,97),(182,70),(141,96),(45,17),(29,149),(134,57)#(166,37),(92,14),(62,9),(137,187),(152,35),(148,52),(20,30),(43,136),(149,116),(28,99),(147,185),(145,18),(33,182),(153,0),(159,70),(18,8),(127,158),(65,95),(14,9),(110,186),(34,81),(183,25),(154,66),(53,98),(33,120),(44,172),(162,138),(1,60),(13,1),(137,12),(112,16),(7,19),(39,6),(1,41),(7,94),(105,90),(155,128),(90,170),(107,26),(134,52),(23,128),(190,90),(106,155),(110,150),(151,72),(19,52),(189,70),(53,93),(132,100),(92,81)"
    p = Puzzle.parse(puz)
    h = p.size
    assert p.block == 1
    assert p.size  == 200
    assert p.vertices['min'] < p.vertices['max']


if __name__ == '__main__':
    utils.testmod()
