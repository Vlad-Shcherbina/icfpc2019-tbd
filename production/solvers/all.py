from production.solvers.greedy import GreedySolver
from production.solvers.rotator import RotatorSolver
from production.solvers.boosty import BoostySolver
from production.solvers.greedy_beam import GreedyBeamSolver

ALL_SOLVERS = {
    'greedy': GreedySolver,
    'rotator': RotatorSolver,
    'boosty': BoostySolver,
    # 'greedy_beam': GreedyBeamSolver,
}


