from production.solvers.greedy import GreedySolver
from production.solvers.rotator import RotatorSolver
from production.solvers.boosty import BoostySolver
from production.solvers.tweaker import TweakerSolver
from production.solvers.greedy_beam import GreedyBeamSolver
from production.solvers.tree_beam import TreeBeamSolver
from production.solvers.insect import InsectSolver

ALL_SOLVERS = {
    'greedy': GreedySolver,
    'rotator': RotatorSolver,
    'boosty': BoostySolver,
    'greedy_beam': GreedyBeamSolver,
    'tree_beam': TreeBeamSolver,
    'tweaker': TweakerSolver,
    'insect': InsectSolver,
}


