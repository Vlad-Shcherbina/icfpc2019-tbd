#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
#include <algorithm>
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

	//static GridTask from_problem(n, )
    // @staticmethod
    // def from_problem(n, with_border=False):
    //     s = utils.get_problem_raw(n)
    //     return GridTask(Task.parse(s), with_border)


};


struct Bot {	
public:
	Pt pos;
	vector<Pt> manipulator;
	vector<Pt> world_manipulator;
	int wheels_timer;
	int drill_timer;
	vector<str> actions;

	Bot(Pt pos) 
	, pos(pos)
	: wheels_timer(0)
	, drill_timer(0)
	, manipulator({ Pt(0, 0), Pt(1, 0), Pt(1, 1), Pt(1, -1) })
	, world_manipulator(manipulator.size())
	{ }
};



struct Game {
public:
	string grid;
	int height;
	int width;
	vector<Bot> bots;


	Game(string task_data) {
		// parse
		
		    // def __init__(self, task: GridTask):
      //   self.task = task
      //   self.grid = task.mutable_grid() # because drill
      //   self.height = task.height
      //   self.width = task.width
      //   self.bots = [Bot(task.start)]
        
      //   self.inventory = Counter()
      //   self.boosters = [b for b in task.boosters if b.code != 'X']
      //   self.clone_spawn = [b.pos for b in task.boosters if b.code == 'X']
      //   self.teleport_spots = []
      //   self.turn = 0

      //   self.wrapped = set()
      //   self.unwrapped = {p for p in self.task.grid_iter() if self.grid[p.y][p.x] == '.'}
      //   self.update_wrapped()
	}


	char& operator[](const Pt& p) {
		return grid[from_pt(p)];
	}

	const char& operator[](const Pt& p) const {
		return grid[from_pt(p)];
	}

	def in_bounds(const Pt& p) {
		return 0 <= p.x && p.x < width && 0 <= p.y && p.y < height;
	}


	string to_string() {
		// EX grid_as_text
		std::stringstream ss;
		for (int y = 0; y < height; y++) {
			for (int x = 0; x < width; x++) {
				ss << grid[y][x] << ' ';
			}
			ss << '\n';
		}
		return ss.str();
	}


	void recalc_manipulator(Bot& b) {
		vector<Pt>& m = bot.manipulator;

		auto  std::for_each(b.manipulator.begin(), b.)
		b.world_manipulator = std::
	}


    def recalc_manipulator(self, bot):
        m = (p + bot.pos for p in bot.manipulator)
        bot.world_manipulator = [p for p in m
            if self.in_bounds(p)
            and geom.visible(self.grid, bot.pos, p)
        ]


    def update_wrapped(self):
        for bot in self.bots:
            self.recalc_manipulator(bot)
            self.wrapped.update(bot.world_manipulator)
            self.unwrapped.difference_update(bot.world_manipulator)


    def is_wrapped(self, p):
        return p in self.wrapped


    def finished(self) -> Optional[int]:
        if self.unwrapped:
            return None
        return self.turn

    def apply_action(self, action: Action, bot_index: int=0):
        # you should always call the zero's bot action explicitely,
        # even if it's Z, since he counts turns
        act = action.s
        bot = self.bots[bot_index]

        if act in 'WSAD':
            for step in range(2 if bot.wheels_timer else 1):
                np = bot.pos + action.WSAD2DIR[act]
                if not self.in_bounds(np):
                    raise InvalidActionException('Can\'t move out of map boundary')

                target = self.grid[np.y][np.x]
                if target != '.':
                    if bot.drill_timer and target == '#':
                        # "im not owned!  im not owned!!", the wall continues to insist
                        # as it slowly shrinks and transforms into a corn cob
                        self.grid[np.y][np.x] = '.'
                        self.unwrapped.add(np)
                    elif step:
                        # second step, OK to fail
                        break
                    else:
                        raise InvalidActionException(f'Can\'t move into a tile: {target!r}')

                bot.pos = np
                booster = [b for b in self.boosters if b.pos == np]
                if booster:
                    [booster] = booster
                    if booster.code in Booster.CODES:
                        self.inventory.update([booster.code])
                        self.boosters.remove(booster)
                self.update_wrapped()

        elif act == 'Z':
            pass

        elif act == 'Q':
            bot.manipulator = [p.rotated_ccw() for p in bot.manipulator]

        elif act == 'E':
            bot.manipulator = [p.rotated_cw() for p in bot.manipulator]

        elif act in 'LFR':
            if not self.inventory[act]:
                raise InvalidActionException('Out of {}s!'.format(Booster.description(act)))
            self.inventory.subtract(act)
            if act == 'L':
                bot.drill_timer = 31
            elif act == 'F':
                bot.wheels_timer = 51
            else:
                self.teleport_spots.append(bot.pos)


        elif act.startswith('B'):
            if not self.inventory['B']:
                raise InvalidActionException('Out of {}s!'.format(Booster.description('B')))
            pt = Pt.parse(act[1:])
            if pt in bot.manipulator:
                raise InvalidActionException("manipulator already there")
            if not any(pt.manhattan_dist(m) == 1 for m in bot.manipulator):
                raise InvalidActionException("manipulator should be adjacent to existing ones")
            bot.manipulator.append(pt)
            self.inventory.subtract('B')


        elif act.startswith('T'):
            self.inventory.subtract('T')
            pt = Pt.parse(act[1:])
            if pt not in self.teleport_spots:
                raise InvalidActionException("no teleport at destination")
            bot.pos = pt


        elif act == 'C':
            if not self.inventory['C']:
                raise InvalidActionException('Out of {}s!'.format(Booster.description('C')))
            if not bot.pos in self.clone_spawn:
                raise InvalidActionException('No clone spawn in current position')
            self.inventory.subtract('C')
            self.bots.append(Bot(bot.pos))


        else:
            raise InvalidActionException(f'Unknown action {action}')


        self.update_wrapped()
        bot.actions.append(action)
        if bot_index == 0:
            self.turn += 1
        for bot in self.bots:
            bot.drill_timer = max(bot.drill_timer - 1, 0)
            bot.wheels_timer = max(bot.wheels_timer - 1, 0)


    def get_actions(self):
        return [b.actions for b in self.bots]




private:
	int from_pt(const Pt& pos) {
		return pos.y * width + pos.x;
	}

	Pt to_pt(int n) {
		return Pt(n % width, n / width);
	}
};





PYBIND11_MODULE(cpp_game, m) {
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
