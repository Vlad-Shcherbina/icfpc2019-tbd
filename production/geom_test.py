from production.geom import *


def test_rasterize_poly():
    poly = [Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]
    assert rasterize_poly(poly) == [Row(y=0, x1=0, x2=1)]
