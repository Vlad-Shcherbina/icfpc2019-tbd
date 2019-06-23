from pytest import raises
from copy import copy, deepcopy

from production import utils
import production.cpp_grid
from production.cpp_grid import Pt, CharGrid

def test_Pt():
    p1 = Pt(1, 2)
    assert str(p1) == '(1,2)'
    assert repr(p1) == 'Pt(1,2)'
    assert p1.x == 1 and p1.y == 2
    p2 = Pt(10, 20)
    assert p1 + p2 == Pt(11, 22)
    assert p1 - p2 == Pt(-9, -18)
    assert -p1 == Pt(-1, -2)
    assert p1.rotated_cw() == p1.rotated_ccw().rotated_ccw().rotated_ccw()
    assert p1.rotated_cw() != p1.rotated_ccw().rotated_ccw()
    assert p1.manhattan_dist(p2) == 9 + 18
    assert deepcopy(p1) == p1
    assert copy(p1) == p1


def test_CharGrid():
    g = CharGrid(3, 5, '#')
    assert g.width == 5 and g.height == 3
    for y in range(3):
        for x in range(5):
            assert g[Pt(x, y)] == '#'
            g[Pt(x, y)] = chr(ord('A') + y * 10 + x)

    for y in range(3):
        for x in range(5):
            assert g[Pt(x, y)] == chr(ord('A') + y * 10 + x)
            assert g.in_bounds(Pt(x, y))

    for p in [(-1, 0), (0, -1), (5, 0), (0, 3)]:
        with raises(IndexError):
            g[Pt(*p)]
            assert not g.in_bounds(Pt(x, y))

    assert g.grid_as_text() == '''\
A B C D E
K L M N O
U V W X Y'''

    for op in [g.copy, lambda: copy(g), lambda: deepcopy(g)]:
        g2 = op()
        assert g2 == g
        g2[Pt(0, 0)] = 'Z'
        assert g[Pt(0, 0)] == 'A'
        assert g2 != g

    g3 = CharGrid([''.join(s.split()) for s in g.grid_as_text().split('\n')])
    assert g3 == g


if __name__ == '__main__':
    utils.testmod()

