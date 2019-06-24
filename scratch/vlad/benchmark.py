import logging
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')
logger = logging.getLogger(__name__)

import time
import cProfile
import subprocess

from production import utils
from production.data_formats import *

from production.solvers.rotator import RotatorSolver

if __name__ == '__main__':
    profile_path = utils.project_root() / 'outputs' / 'profile'
    callgraph_path = utils.project_root() / 'outputs' / 'callgraph.png'

    task = utils.get_problem_raw(100)
    solver = RotatorSolver([])

    start = time.time()
    cProfile.run('solver.solve(task)', profile_path)
    logging.info(f'it took {time.time() - start}s')

    subprocess.check_call(
        f'gprof2dot -f pstats -n 2 {profile_path} | dot -Tpng -o {callgraph_path}', shell=True)
    print(f'see {callgraph_path}')
