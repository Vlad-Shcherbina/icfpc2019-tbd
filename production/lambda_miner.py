import logging
logger = logging.getLogger(__name__)
import zlib
import json
from typing import Optional

from production import db
from production import utils
from production import lambda_chain


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

    block = lambda_chain.get_block_info()

    upload_current_task(conn, block)
    sol = find_best_solution(conn, f'block-{block.number:04d}')

    age = block.age_in_seconds
    logging.info(f'block {block.number} age {age}s')
    # TODO: only submit for old enough blocks

    if sol is not None:
        task = TODO
        lambda_chain.submit(block.number, solution=sol, task=task)


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
