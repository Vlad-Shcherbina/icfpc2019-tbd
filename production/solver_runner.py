'''
Utility to locally run solvers that conform to production/solvers/interface.py
for debugging purposes.

Results are not uploaded to the DB.
'''

import zlib
import sys
import logging
logger = logging.getLogger(__name__)

from production import db
from production.solvers import interface
from production.solvers.all import ALL_SOLVERS
from production.golden import validate


def main():
    if len(sys.argv) < 2 :
        print('Usage:')
        print('    python -m production.solver_runner <solver> [<solver args>...]')
        print(f'where <solver> is one of {ALL_SOLVERS.keys()}')
        sys.exit(1)

    conn = db.get_conn()
    cur = conn.cursor()

    solver = ALL_SOLVERS[sys.argv[1]](sys.argv[2:])
    logger.info(f'Solver scent: {solver.scent()!r}')

    cur.execute('''
        SELECT id
        FROM tasks
    ''')
    problem_ids = [id for [id] in cur]
    logger.info(f'Problems to solve: {problem_ids}')

    for problem_id in problem_ids:
        logger.info('-' * 50)
        cur.execute(
            'SELECT name, data, extra FROM tasks WHERE id = %s',
            [problem_id])
        [problem_name, task_data, extra] = cur.fetchone()
        logger.info(f'Solving task/{problem_id} ({problem_name}, {extra["legend"]})...')

        task_data = zlib.decompress(task_data).decode()
        sr = solver.solve(task_data)

        if sr.extra:
            logging.info(f'extra = {sr.extra}')

        if isinstance(sr.data, interface.Pass):
            logging.info('Solver passed')
        elif isinstance(sr.data, interface.Fail):
            logging.warning('Solver failed')
        else:
            logging.info(f'Expected score = {sr.expected_score}, checking ...')

            res = validate.run(task_data, sr.data)
            assert res.time is not None, res

            if sr.expected_score is None:
                logging.info(f'Actual score   = {res.time}')
            else:
                if sr.expected_score != res.time:
                    logging.error(f'Actual score   = {res.time}, the solver was wrong!!!')
                else:
                    logging.info('Validation ok')

    logger.info('All done')


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    from importlib.util import find_spec
    if find_spec('hintcheck'):
        import hintcheck
        hintcheck.hintcheck_all_functions()

    main()
