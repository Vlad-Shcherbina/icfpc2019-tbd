from production.geom import *


def test_rasterize_poly():
    poly = [Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(0, 1)]
    assert rasterize_poly(poly) == [Row(y=0, x1=0, x2=1)]


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

    s = utils.get_problem_raw(12)
    t = Task.parse(s)
    bb = poly_bb(t.border)

    grid = [['#'] * (bb.x2 - bb.x1) for y in range(bb.y1, bb.y2)]

    for row in rasterize_poly(t.border):
        for x in range(row.x1, row.x2):
            assert grid[row.y - bb.y1][x - bb.x1] == '#'
            grid[row.y - bb.y1][x - bb.x1] = '.'


    for obstacle in t.obstacles:
        for row in rasterize_poly(obstacle):
            for x in range(row.x1, row.x2):
                assert grid[row.y - bb.y1][x - bb.x1] == '.'
                grid[row.y - bb.y1][x - bb.x1] = '#'
    
    assert visible(grid, Pt(6, 2), Pt(6, 6))
    assert not visible(grid, Pt(2, 2), Pt(2, 6))

    # corners
    assert visible(grid, Pt(1, 2), Pt(4, 3))
    assert visible(grid, Pt(4, 3), Pt(1, 2))
    assert visible(grid, Pt(5, 2), Pt(2, 3))
    assert visible(grid, Pt(2, 3), Pt(5, 2))
    assert visible(grid, Pt(1, 1), Pt(5, 5))


if __name__ == '__main__':
    test_visibility()