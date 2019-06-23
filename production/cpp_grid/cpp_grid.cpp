//#include <stdio.h>
#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#include <functional>
#include <vector>
#include <string>
#include <sstream>

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
    CharGrid(const CharGrid&) = delete;
    CharGrid(CharGrid&&) = delete;


    CharGrid(int a_height, int a_width, char _default=0):
        height(a_height), width(a_width), data(height * width, _default)
    { }


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
};


PYBIND11_MODULE(cpp_grid_ext, m) {
    m.doc() = "pybind11 mine grid";

    py::class_<Pt>(m, "Pt")
        .def(py::init<int, int>())
        .def(py::self + py::self)
        .def(py::self - py::self)
        .def(py::self == py::self)
        .def(py::self != py::self)
        .def(-py::self)
        .def("rotated_cw", &Pt::rotated_cw)
        .def("rotated_ccw", &Pt::rotated_ccw)
        .def("manhattan_dist", &Pt::manhattan_dist)
        .def("__str__", [](const Pt & p) { return to_string(p); })
        .def("__repr__", [](const Pt & p) { return "Pt" + to_string(p); })
        .def("__hash__", [](const Pt & p) { return p.hash(); })
        .def_readonly("x", &Pt::x)
        .def_readonly("y", &Pt::y)
        ;

    py::class_<CharGrid>(m, "CharGrid")
        .def(py::init<int, int>())
        .def(py::init<int, int, char>())
        .def_property_readonly("width", &CharGrid::get_width)
        .def_property_readonly("height", &CharGrid::get_height)
        .def("__getitem__", [](const CharGrid &a, const Pt& b) {
                return a[b];
            })
        .def("__setitem__", [](CharGrid &a, const Pt& b, char c) {
                a[b] = c;
            })
        .def("in_bounds", &CharGrid::in_bounds)
        .def("grid_as_text", &CharGrid::grid_as_text)
        .def("__str__", &CharGrid::grid_as_text)
        ;
}
