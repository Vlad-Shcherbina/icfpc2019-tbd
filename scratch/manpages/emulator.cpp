#include <iostream>
#include <vector>

#include <boost/polygon/polygon.hpp>
#include <cassert>

namespace gtl = boost::polygon;
using namespace boost::polygon::operators;

typedef gtl::polygon_data<int> Polygon;
typedef gtl::polygon_traits<Polygon>::point_type Point;

struct Desc {
};

int main() {
	Point pts[] = { gtl::construct<Point>(0, 0),
	                gtl::construct<Point>(10, 0),
	gtl::construct<Point>(10, 10),
	gtl::construct<Point>(0, 10) };
	Polygon poly;
	gtl::set_points(poly, pts, pts+4);

  assert (gtl::area(poly) == 100.0f);
}
