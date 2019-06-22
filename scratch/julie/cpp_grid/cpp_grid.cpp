#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#include <vector>
#include <string>
#include <sstream>

using std::vector;
using std::string;

struct Pt {
public:
	int x;
	int y;

	Pt() : x(0), y(0)
	{}

	Pt(int x, int y) : x(x), y(y)
	{}

	Pt operator+(const Pt& other) const {
		return Pt(this->x + other.x, this->y + other.y);
	}

	Pt operator-(const Pt& other) const {
		return Pt(this->x - other.x, this->y - other.y);
	}

	void operator+=(const Pt& other) {
		this->x += other.x;
		this->y += other.y;
	}

	void operator-=(const Pt& other) {
		this->x -= other.x;
		this->y -= other.y;
	}

	bool operator==(const Pt& other) const {
		return this->x== other.x && this->y == other.y;
	}

	bool operator!=(const Pt& other) const {
		return !(*this == other);
	}
};


struct GridTask {
public:
	Pt start;
	//vector<Booster> boosters;
	vector<vector<string>> grid;
	int width;
	int height;

	//static GridTask from_problem(n, )
    // @staticmethod
    // def from_problem(n, with_border=False):
    //     s = utils.get_problem_raw(n)
    //     return GridTask(Task.parse(s), with_border)


    GridTask(vector<vector<string>> g) {
    	height = g.size();
    	width = g[0].size();
    	grid = g;
    }


    string& operator[](const Pt& pos) {
    	return grid[pos.y][pos.x];
    }


    const string& operator[](const Pt& pos) const {
    	return grid[pos.y][pos.x];
    }


	string grid_as_text() {
		std::stringstream ss;
		// for (int i = height - 1; i >= 0; i--)
		for (int y = 0; y < height; y++) {
			for (int x = 0; x < width; x++) {
				ss << grid[y][x] << ' ';
			}
			ss << '\n';
		}
		return ss.str();
	}
};


PYBIND11_MODULE(cpp_grid, m) {
	m.doc() = "pybind11 mine grid";

	py::class_<Pt>(m, "Pt")
		.def(py::init<int, int>())
		.def(py::self + py::self)
		.def(py::self += py::self)
		.def(py::self - py::self)
		.def(py::self -= py::self)
		.def(py::self == py::self)
		.def(py::self != py::self)
	;

	py::class_<GridTask>(m, "GridTask")
		.def(py::init<const vector<vector<string>>&>())
		.def("__getitem__", [](const GridTask &a, const Pt& b) {
    		return a[b];
		}, py::is_operator())
		.def("__setitem__", [](GridTask &a, const Pt& b) {
    		return a[b];
		}, py::is_operator())
		.def("grid_as_text", &GridTask::grid_as_text)
	;
}
