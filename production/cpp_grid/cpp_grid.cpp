#include "basics.h"

//#include <stdio.h>
#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#include <functional>
#include <vector>
#include <string>
#include <sstream>

#include <algorithm>
#include <utility>
#include <unordered_map>
#include <cassert>

using std::vector;
using std::string;

using CharGrid = Grid<char>;
using ByteGrid = Grid<uint8_t>; // unsigned
using IntGrid = Grid<int>;

// ---------------- BFS walks -----------------------

class BFS_BaseWalker {
public:
    bool stop;

    BFS_BaseWalker() : stop(false) {}

    virtual void run_current(const Pt& p) = 0;
    virtual void run_neighbour(const Pt& p) = 0;
    virtual bool is_suitable(const Pt& p) = 0;
};



// NOT TESTED! might be fallacious
void bfs(CharGrid& grid, Pt start, BFS_BaseWalker* walker) {
    vector<Pt> frontier = { start };
    while (frontier.size() > 0) {
        vector<Pt> new_frontier;

        for (int i = 0; i < frontier.size(); i++) {
            Pt p = frontier[i];
            walker->run_current(p);
            if (walker->stop) return;

            for (Pt d : {Pt(0, 1), Pt(1, 0), Pt(0, -1), Pt(-1, 0)}) {
                Pt n = p + d;
                if (!grid.in_bounds(n) || !walker->is_suitable(n)) {
                    continue;
                }
                walker->run_neighbour(n);
                if (walker->stop) return;
                new_frontier.push_back(n);
            }
        }
        frontier = new_frontier;
    }
}

// char pt_to_direction(const Pt& p) {
//     if (p == Pt(0, 1))       return 'W';
//     else if (p == Pt(1, 0))  return 'D';
//     else if (p == Pt(0, -1)) return 'S';
//     else if (p == Pt(-1, 0)) return 'A';
//     else if (p == Pt(0, 0))  return 'Z';
//     else assert(false);
// }


class PathFinder : public BFS_BaseWalker {
public:
    CharGrid& grid;
    Pt src;
    Pt dest;
    Pt last;
    std::unordered_map<Pt, vector<Pt>> paths;
    vector<Pt> result;

    PathFinder(CharGrid& grid, Pt src, Pt dest)
    : grid(grid)
    , src(src)
    , dest(dest)
    , last(src)
    {
        paths[src] = { src };
    }

    bool is_suitable(const Pt& p) override {
        return grid[p] == '.'
            && paths.find(p) == paths.end();
    }

    void run_current(const Pt& p) override {
        last = p;
    }

    void run_neighbour(const Pt& p) override {
        paths[p] = paths[last];
        paths[p].push_back(p);
        if (p == dest) {
            stop = true;
            result = paths[p];
        }
    }
};



std::ostream& operator<<(std::ostream& out, Pt p) {
    out << "(" << p.x << ", " << p.y << ')';
    return out;
}


class BoostFinder : public BFS_BaseWalker {
public:
    CharGrid& grid;
    CharGrid& wrapped;
    vector<Pt> border;
    int countdown;
    vector<Pt>& boosters;
    vector<Pt> manips;
    Pt start;
    Pt last;
    Pt candidate;
    std::unordered_map<Pt, std::pair<float, vector<Pt>>> paths;
    std::unordered_map<Pt, float> costs;
    float boost_tradeoff;
    float wrap_penalty;

    BoostFinder(CharGrid& grid, CharGrid& wrapped,
                Pt start, vector<Pt> manips,
                vector<Pt> border, vector<Pt>& boosters,
                float boost_tradeoff, float wrap_penalty)
    : grid(grid)
    , wrapped(wrapped)
    , border(border)
    , countdown((int)border.size())
    , boosters(boosters)
    , start(start)
    , last(start)
    , boost_tradeoff(boost_tradeoff)
    , wrap_penalty(wrap_penalty)
    , manips(manips)
    , candidate(-1, -1)
    {
        paths[start] = std::make_pair(0.0f, vector<Pt>());
        paths[start].second.push_back(start);
    }

    bool is_suitable(const Pt& p) override {
        return grid[p] == '.'
            && paths.find(p) == paths.end();
    }


    void run_current(const Pt& p) override {
        last = p;
    }


    void add_penalty() {
        for (auto kv : paths) {
            Pt p = kv.first;
            for (Pt m : manips) {
                Pt pm = p + m;
                if (!wrapped.in_bounds(pm)) continue;
                if (wrapped[pm] == '.') continue;
                paths[pm].first += wrap_penalty;
            }

            if (wrapped[p] == '#') continue;
            if (candidate == Pt(-1, -1) || paths[p].first < paths[candidate].first) {
                candidate = p;
            }
        }
    }


    void run_neighbour(const Pt& p) override {
        paths[p].first = paths[last].first + 1;
        paths[p].second = paths[last].second;
        paths[p].second.push_back(p);

        if (std::find(boosters.begin(), boosters.end(), p) != boosters.end())
            paths[p].first -= boost_tradeoff;

        auto b_it = std::find(border.begin(), border.end(), p);
        if (b_it != border.end()) {
            countdown -= 1;
        }

        if (countdown == 0) {
            add_penalty();
            stop = true;
        }
    }

};


// ---------------- BFS walks -----------------------


template<class TGrid>
void register_grid(py::module &m, const char * name) {
    py::class_<TGrid>(m, name)
        .def(py::init<int, int>())
        .def(py::init<int, int, TGrid::TValue>())
        .def(py::init<const TGrid&>())
        .def(py::init<const vector<string>&>())
        .def_property_readonly("width", &TGrid::get_width)
        .def_property_readonly("height", &TGrid::get_height)
        .def("__getitem__", [](const TGrid &a, const Pt& b) {
                return a[b];
            })
        .def("__setitem__", [](TGrid &a, const Pt& b, TGrid::TValue c) {
                a[b] = c;
            })
        .def("in_bounds", &TGrid::in_bounds)
        .def("update_values", &TGrid::update_values)
        // all copies are deep
        .def("copy", [](const TGrid & a) { return TGrid(a); })
        .def("__copy__", [](const TGrid & a) { return TGrid(a); })
        .def("__deepcopy__", [](const TGrid & a, py::dict & memo) { return TGrid(a); })
        .def("grid_as_text", &TGrid::grid_as_text)
        .def("__str__", &TGrid::grid_as_text)
        .def(py::self == py::self)
        .def(py::self != py::self)
        ;
}


PYBIND11_MODULE(cpp_grid_ext, m) {
    m.doc() = "pybind11 mine grid";

    py::class_<Pt>(m, "Pt")
        .def(py::init<int, int>())
        .def(py::self + py::self)
        .def(py::self - py::self)
        .def(py::self == py::self)
        .def(py::self != py::self)
        .def(py::self * int())
        .def(-py::self)
        .def("rotated_cw", &Pt::rotated_cw)
        .def("rotated_ccw", &Pt::rotated_ccw)
        .def("manhattan_dist", &Pt::manhattan_dist)
        .def("__str__", [](const Pt & p) { return to_string(p); })
        .def("__repr__", [](const Pt & p) { return "Pt" + to_string(p); })
        .def("__hash__", [](const Pt & p) { return p.hash(); })
        // we are immutable so return self as copy
        .def("__copy__", [](const Pt & p) { return p; })
        .def("__deepcopy__", [](const Pt & p, py::dict & memo) { return p; })
        .def_readonly("x", &Pt::x)
        .def_readonly("y", &Pt::y)
        ;

    register_grid<CharGrid>(m, "CharGrid");
    register_grid<ByteGrid>(m, "ByteGrid");
    register_grid<IntGrid>(m, "IntGrid");

    m.def("pathfind", [](CharGrid& grid, Pt start, Pt end){
        auto executor = new PathFinder(grid, start, end);
        bfs(grid, start, executor);
        vector<Pt> result = executor->result;
        delete executor;
        return result;
    });

    m.def("boostfind", [](CharGrid& grid,
                          CharGrid& wrapped,
                          Pt start,
                          vector<Pt> manips,
                          const vector<Pt>& borders,
                          vector<Pt>& boosts,
                          float boost_tradeoff,
                          float wrap_penalty) {
        BoostFinder* executor = new BoostFinder(grid, wrapped, start, manips,
                                    borders, boosts, boost_tradeoff, wrap_penalty);
        bfs(grid, start, executor);
        vector<Pt> result = executor->paths[executor->candidate].second;
        delete executor;
        return result;
    });
}
