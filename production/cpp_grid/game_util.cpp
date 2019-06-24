#include "basics.h"

//#include <stdio.h>
#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
namespace py = pybind11;


// mechanically translated from Python impl
bool visible(const CharGrid &grid, Pt p1, Pt p2) {
    Pt dist = p2 - p1;
    double q = 1.0 / ((abs(dist.x) + abs(dist.y)) * 2 + 1);
    double move_x = dist.x * q;
    double move_y = dist.y * q;

    double current_x = p1.x + 0.5;
    double current_y = p1.y + 0.5;

    while (true) {
        current_x += move_x;
        current_y += move_y;
        Pt p((int)current_x, (int)current_y);
        if (grid[p] != '.') {
            return false;
        }
        if (p == p2) {
            return true;
        }
    }
    assert(false);
}


void init_game_util_bindings(py::module &m) {
    m.def("visible", &visible);
}
