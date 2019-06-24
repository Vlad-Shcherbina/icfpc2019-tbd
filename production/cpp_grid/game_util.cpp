#include "basics.h"
#include "debug.h"
#include "pretty_printing.h"

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

vector<Pt> manipulators_will_wrap(
        const CharGrid &grid,
        const ByteGrid &wrapped,
        Pt worker_pos, const vector<Pt> &manips) {
    vector<Pt> result;
    for (Pt m : manips) {
        Pt pt = worker_pos + m;
        if (grid.in_bounds(pt) && !wrapped[pt] && visible(grid, worker_pos, pt)) {
            result.push_back(pt);
        }
    }
    return result;
}


const int INF = 9999;

const vector<Pt> dirs = {Pt(1, 0), Pt(0, 1), Pt(-1, 0), Pt(0, -1)};

struct DistanceField {
    CharGrid grid;
    IntGrid dist;

    DistanceField(const CharGrid &grid)
    : grid(grid), dist(grid.get_height(), grid.get_width(), INF) {}

    void build(const vector<Pt> &starts) {
        vector<Pt> front = starts;
        for (Pt p : front) {
            assert(grid[p] == '.');
            dist[p] = 0;
        }
        vector<Pt> new_front;
        int cur_dist = 1;
        while (!front.empty()) {
            for (Pt p : front) {
                for (Pt d : dirs) {
                    Pt p2 = p + d;
                    if (grid.in_bounds(p2) && grid[p2] == '.') {
                        if (dist[p2] == INF) {
                            dist[p2] = cur_dist;
                            new_front.push_back(p2);
                        }
                    }
                }
            }
            cur_dist++;
            using std::swap;
            swap(front, new_front);
            new_front.clear();
        }
    }
};


void init_game_util_bindings(py::module &m) {
    m.def("visible", &visible);
    m.def("manipulators_will_wrap", &manipulators_will_wrap);

    py::class_<DistanceField>(m, "DistanceField")
        .def(py::init<const CharGrid &>())
        .def("build", &DistanceField::build)
        .def_readonly("dist", &DistanceField::dist)
        ;
}
