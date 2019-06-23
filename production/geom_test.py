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

    for row in vis:
        print(' '.join(row))
    # no comparison with expected because it's too large


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
    expected_vis = [list(row.replace(' ', '')) for row in expected_vis]
    grid = deepcopy(expected_vis)
    eye = None
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c in 'o+':
                row[x] = '.'
            if c == 'o':
                assert eye is None
                eye = Pt(x, y)

    vis = render_visibility_grid(grid, eye)
    for row in vis:
        print(' '.join(row))

    assert vis == expected_vis


def render_visibility_grid(grid, eye):
    '''
    o   eye location
    .   visible
    +   not visible
    '''
    vis = deepcopy(grid)
    vis[eye.y][eye.x] = 'o'
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            v = visible(grid, eye, Pt(x, y))
            v2 = visible(grid, Pt(x, y), eye)
            assert v == v2
            if grid[y][x] == '#':
                assert not v
            elif grid[y][x] == '.':
                if not v:
                    vis[y][x] = '+'
            else:
                assert False, grid[y][x]
    return vis


if __name__ == '__main__':
    utils.testmod()
