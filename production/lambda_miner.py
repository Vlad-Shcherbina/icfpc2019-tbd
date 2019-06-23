import logging
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
logger = logging.getLogger(__name__)

import time
import zlib
import json
from typing import Optional

from production import db
from production import utils
from production import lambda_chain
from production.data_formats import *
from production.golden import validate
from production import puzzle_solver


def find_best_solution(conn, problem_name) -> Optional[str]:
    cur = conn.cursor()
    cur.execute('''
    SELECT
        solutions.id, solutions.score, solutions.data
    FROM tasks
    JOIN solutions ON solutions.task_id = tasks.id
    WHERE tasks.name = %s AND solutions.status = 'DONE'
    ORDER BY solutions.score ASC
    LIMIT 1
    ''', [problem_name])

    for id, score, data in cur:
        logger.info(f'best solution sol/{id} with score {score}')
        return zlib.decompress(data).decode()

    logger.info(f'no solutions for {problem_name}')
    return None


def upload_current_task(conn, block):
    cur = conn.cursor()

    name = f'block-{block.number:04d}'
    data = zlib.compress(block.task.encode())
    extra = {}

    cur.execute('''
        INSERT INTO tasks(
            name, data, extra, invocation_id, time)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT DO NOTHING
        RETURNING id
        ''',
        [name, data, json.dumps(extra), db.get_this_invocation_id(conn)])
    res = cur.fetchall()
    if res:
        conn.commit()
        [[task_id]] = res
        logger.info(f'Uploaded {name!r} as /task/{task_id}')
    else:
        logger.info(f'Task {name!r} already exists')


def main():
    conn = db.get_conn()

    while True:
        block = lambda_chain.get_block_info()

        upload_current_task(conn, block)

        f = utils.project_root() / 'outputs' / f'block-{block.number:04d}.cond'
        f.write_text(block.puzzle)
        logging.info(f'Block puzzle saved to {f}')

        task = puzzle_solver.solve(Puzzle.parse(block.puzzle))
        task = str(task)
        logging.info(f'Validating puzzle solution...')
        result = validate.puz(block.puzzle, task)
        logging.info(result)
        assert result == 'ok'

        block_submitted = False
        while True:
            new_block = lambda_chain.get_block_info()
            logging.info(f'block age: {int(new_block.age_in_seconds)}s')
            if new_block.number != block.number:
                logging.info('new block appeared   ' + '-' * 30)
                break

            if not block_submitted:
                sol = find_best_solution(conn, f'block-{block.number:04d}')
                if sol is not None:
                    lambda_chain.submit(block.number, solution=sol, task=task)
                    block_submitted = True

            logging.info('waiting...')
            db.record_this_invocation(conn, status=db.KeepRunning(60))
            conn.commit()
            time.sleep(10)


if __name__ == '__main__':
    from importlib.util import find_spec
    if find_spec('hintcheck'):
        import hintcheck
        hintcheck.hintcheck_all_functions()

    main()
