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


struct Pt {
    int x;
    int y;

    Pt(int a_x, int a_y) : x(a_x), y(a_y)
    {}


    Pt operator+(const Pt& other) const {
        return Pt(x + other.x, y + other.y);
    }


    Pt operator-(const Pt& other) const {
        return Pt(x - other.x, y - other.y);
    }


    Pt operator-() const {
        return Pt(-x, -y);
    }


    bool operator==(const Pt& other) const {
        return x == other.x && y == other.y;
    }


    bool operator!=(const Pt& other) const {
        return !(*this == other);
    }


    Pt operator*(int n) const {
        return Pt(this->x * n, this->y * n);
    }


    Pt rotated_ccw() const {
        return {-y, x};
    }


    Pt rotated_cw() const {
        return {y, -x};
    }


    int manhattan_dist(const Pt & other) const {
        return abs(x - other.x) + abs(y - other.y);
    }


    size_t hash() const {
        // In case some people use 32 bit Python, avoid truncation
        return ((long long)x << 16) + y;
    }
};


// custom specialization of strict hash can be injected in namespace std
namespace std
{
    template<> struct hash<Pt>
    {
        size_t operator()(const Pt & p) const noexcept
        {
            return std::hash<long long>()(p.hash());
        }
    };
}


// this can't be injected in std
const string to_string(const Pt & p) {
    return string("(" + std::to_string(p.x) + "," + std::to_string(p.y) + ")");
}


class CharGrid {
    int height;
    int width;

    vector<char> data;

public:

    CharGrid() = delete;
    CharGrid(const CharGrid&) = default;
    CharGrid(CharGrid&&) = default;


    CharGrid(int a_height, int a_width, char _default=0):
        height(a_height), width(a_width), data(height * width, _default)
    { }

    
    CharGrid(const vector<string> & init):
        height((int)init.size()), width((int)init.at(0).size()), data(height * width)
    {
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                data[y * width + x] = init[y].at(x);
            }
        }
    }


    int get_height() const {
        return height;
    }


    int get_width() const {
        return width;
    }


    bool in_bounds(const Pt & pos) const {
        return 0 <= pos.x && pos.x < width &&
               0 <= pos.y && pos.y < height;
    }


    char& operator[](const Pt& pos) {
        if (in_bounds(pos)) {
            return data[pos.y * width + pos.x];
        }
        throw pybind11::index_error("index=" + to_string(pos) + ", width_height=" + to_string(Pt(width, height)));
    }


    char operator[](const Pt& pos) const {
        return (*const_cast<CharGrid*>(this))[pos];
    }


    string grid_as_text() const {
        string res;
        for (int row = 0; row < height; row++) {
            if (row != 0) res += '\n';
            for (int col = 0; col < width; col++) {
                if (col != 0) res += ' ';
                res += (*this)[Pt(col, row)];
            }
        }
        return res;
    }

    bool operator==(const CharGrid& other) const {
        return height == other.height && width == other.width && data == other.data;
    }


    bool operator!=(const CharGrid& other) const {
        return !(*this == other);
    }

    CharGrid copy() {
        return *this;
    }
};


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
    , countdown(border.size())
    , boosters(boosters)
    , start(start)
    , last(start)
    , boost_tradeoff(boost_tradeoff)
    , wrap_penalty(wrap_penalty)
    , manips(manips)
    , candidate(-1, -1)
    {
        paths[start] = std::make_pair(0, vector<Pt>());
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

    py::class_<CharGrid>(m, "CharGrid")
        .def(py::init<int, int>())
        .def(py::init<int, int, char>())
        .def(py::init<const CharGrid&>())
        .def(py::init<const vector<string>&>())
        .def_property_readonly("width", &CharGrid::get_width)
        .def_property_readonly("height", &CharGrid::get_height)
        .def("__getitem__", [](const CharGrid &a, const Pt& b) {
                return a[b];
            })
        .def("__setitem__", [](CharGrid &a, const Pt& b, char c) {
                a[b] = c;
            })
        .def("in_bounds", &CharGrid::in_bounds)
        // all copies are deep
        .def("copy", [](const CharGrid & a) { return CharGrid(a); })
        .def("__copy__", [](const CharGrid & a) { return CharGrid(a); })
        .def("__deepcopy__", [](const CharGrid & a, py::dict & memo) { return CharGrid(a); })
        .def("grid_as_text", &CharGrid::grid_as_text)
        .def("__str__", &CharGrid::grid_as_text)
        .def(py::self == py::self)
        .def(py::self != py::self)
        ;

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
