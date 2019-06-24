// Basic data types: point, grid.

#pragma once

#include <vector>
#include <string>

using namespace std;  // I know, but reasons

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


inline const string my_to_string(const Pt & p) {
    return string("(" + std::to_string(p.x) + "," + std::to_string(p.y) + ")");
}

inline const string my_to_string(char x) {
    return string(1, x);
}

inline const string my_to_string(uint8_t x) {
    return std::to_string(x);
}

inline const string my_to_string(int x) {
    return std::to_string(x);
}


template<typename T>
class Grid {
    int height;
    int width;

    static_assert(!std::is_same<T, bool>::value);
    vector<T> data;

public:

    using TValue = T;
    using TGrid = Grid<T>;

    Grid() = delete;
    Grid(const TGrid &) = default;
    Grid(TGrid &&) = default;


    Grid(int a_height, int a_width, T _default=0):
        height(a_height), width(a_width), data(height * width, _default)
    { }


    Grid(const vector<string> & init):
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


    T& operator[](const Pt& pos) {
        if (in_bounds(pos)) {
            return data[pos.y * width + pos.x];
        }
        throw pybind11::index_error("index=" + my_to_string(pos) + ", width_height=" + my_to_string(Pt(width, height)));
    }


    T operator[](const Pt& pos) const {
        return (*const_cast<TGrid*>(this))[pos];
    }


    int update_values(const std::vector<Pt> & points, T value) {
        int updated = 0;
        for (auto p : points) {
            if ((*this)[p] != value) {
                (*this)[p] = value;
                updated++;
            }
        }
        return updated;
    }

    
    string grid_as_text() const {
        string res;
        for (int row = 0; row < height; row++) {
            if (row != 0) res += '\n';
            for (int col = 0; col < width; col++) {
                if (col != 0) res += ' ';
                res += my_to_string((*this)[Pt(col, row)]);
            }
        }
        return res;
    }

    bool operator==(const TGrid& other) const {
        return height == other.height && width == other.width && data == other.data;
    }


    bool operator!=(const TGrid& other) const {
        return !(*this == other);
    }

    TGrid copy() {
        return *this;
    }
};

using CharGrid = Grid<char>;
using ByteGrid = Grid<uint8_t>; // unsigned
using IntGrid = Grid<int>;
