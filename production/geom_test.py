import pytest

from production.geom import *
from production import utils
from production.data_formats import Task, GridTask
from copy import deepcopy


def test_rasterize_poly():
    poly = [Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(0, 1)]
    assert rasterize_poly(poly) == [Row(y=0, x1=0, x2=1)]


def test_pt_in_poly():
    poly = [Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(0, 1)]
    assert pt_in_poly(Pt(0, 0), poly)
    assert not pt_in_poly(Pt(1, 0), poly)


@pytest.mark.parametrize('cells', [
    {Pt(3, 7)},
    {Pt(3, 7), Pt(4, 7)},
    {Pt(3, 7), Pt(4, 7), Pt(4, 8)},
])
def test_trace_poly(cells):
    poly = trace_poly(cells)
    print(poly)
    cells2 = {Pt(x, row.y) for row in rasterize_poly(poly) for x in range(row.x1, row.x2)}
    assert cells == cells2


def test_poly_without_redundant_vertices():
    #      #
    #    # #
    poly = [Pt(0, 0), Pt(1, 0), Pt(2, 0), Pt(2, 1), Pt(2, 2), Pt(1, 2), Pt(1, 1), Pt(0, 1)]
    expected_poly = [Pt(0, 0), Pt(2, 0), Pt(2, 2), Pt(1, 2), Pt(1, 1), Pt(0, 1)]
    assert poly_without_redundant_vertices(poly) == expected_poly


def test_visibility():
    # Corner of 11th task
    #   012345678
    # 0 #...##...
    # 1 #...##...
    # 2 #...##...
    # 3 ###.##...
    # 4 ##.......
    # 5 ##.......
    # 6 ##.......

    t = GridTask.from_problem(12)
    grid = t.mutable_grid()

    assert visible(grid, Pt(6, 2), Pt(6, 6))
    assert not visible(grid, Pt(2, 2), Pt(2, 6))

    # corners
    assert visible(grid, Pt(1, 2), Pt(4, 3))
    assert visible(grid, Pt(4, 3), Pt(1, 2))
    assert visible(grid, Pt(5, 2), Pt(2, 3))
    assert visible(grid, Pt(2, 3), Pt(5, 2))
    assert visible(grid, Pt(1, 1), Pt(5, 5))

    vis = render_visibility_grid(grid, Pt(13, 12))


def test_visibility_small():
    check_vis([
        '. . + + +',
        '. . # + .',
        '. o . . .',
        '. . . . .',
    ])


def test_visibility_enclosed():
    check_vis([
        '. + + + .',
        '+ . # . +',
        '+ # o # +',
        '+ . # . +',
        '. + + + .',
    ])


def test_visibility_hor():
    check_vis([
        '. . . . .',
        '+ . . . +',
        '+ # o # +',
        '+ . . . +',
        '. . . . .',
    ])


def test_visibility_ver():
    check_vis([
        '. + + + .',
        '. . # . .',
        '. . o . .',
        '. . # . .',
        '. + + + .',
    ])


def check_vis(expected_vis):
    expected_vis = CharGrid([row.replace(' ', '') for row in expected_vis])
    grid = expected_vis.copy()
    eye = None
    for p, c in enumerate_grid(grid):
        if c in 'o+':
            grid[p] = '.'
        if c == 'o':
            assert eye is None
            eye = p

    vis = render_visibility_grid(grid, eye)
    print(vis.grid_as_text())
    assert vis == expected_vis


def render_visibility_grid(grid: CharGrid, eye):
    '''
    o   eye location
    .   visible
    +   not visible
    '''
    print(grid)
    vis = grid.copy()
    vis[eye] = 'o'
    for p, c in enumerate_grid(grid):
        v = visible(grid, eye, p)
        v2 = visible(grid, p, eye)
        assert v == v2
        if c == '#':
            assert not v
        elif c == '.':
            if not v:
                vis[p] = '+'
        else:
            assert False, c
    return vis


if __name__ == '__main__':
    utils.testmod()
