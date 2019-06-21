from production.geom import *


def test_rasterize_poly():
    poly = [Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(0, 1)]
    assert rasterize_poly(poly) == [Row(y=0, x1=0, x2=1)]
