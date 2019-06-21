import sys
import random
import time
import json
import zlib
from typing import Optional, Any, List, Dict
from dataclasses import dataclass
import multiprocessing
import multiprocessing.queues
import argparse
import logging
import traceback
from io import StringIO
logger = logging.getLogger(__name__)

from production import db
from production import utils
from production.solvers import interface
from production.golden import validate
from production.solvers.all import ALL_SOLVERS

Json = dict


@dataclass
class Result:
    '''Information about the solution that we want to write to the DB.'''
    status: str  # see db.py, table 'solutions' for explanation
    scent: str
    score: Optional[int]
    solution: Optional[str]
    extra: Json


def put_solution(conn, task_id: int, result: Result):
    assert result.status in ('DONE', 'PASS', 'FAIL', 'CHECK_FAIL'), result.status

    if result.solution is not None:
        data = zlib.compress(result.solution.encode())
    else:
        data = None
    extra = json.dumps(result.extra)

    cur = conn.cursor()
    cur.execute('''
        INSERT INTO solutions(
            scent, status, score, data, extra,
            task_id, invocation_id, time)
        VALUES(%s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING id
        ''',
        [result.scent, result.status, result.score, data, extra,
         task_id, db.get_this_invocation_id(conn)])
    [solution_id] = cur.fetchone()
    logging.info(f'Recorded as sol/{solution_id}')


def solve(solver: interface.Solver, task_data: str) -> Result:
    logging.info('Solving...')
    start = time.time()
    try:
        sr = solver.solve(task_data)
    except KeyboardInterrupt:
        raise
    except:
        exc = StringIO()
        traceback.print_exc(file=exc)
        sr = interface.SolverResult(
            data=interface.Fail(),
            expected_score=None,
            extra=dict(tb=exc.getvalue()))
    solver_time = time.time() - start
    logging.info(f'It took {solver_time}')
    if isinstance(sr.data, interface.Pass):
        logging.info(f'Solver passed: {sr.extra}')
        return Result(
            scent=solver.scent(), status='PASS', score=None, solution=None,
            extra=dict(solver=sr.extra, solver_time=solver_time))
    elif isinstance(sr.data, interface.Fail):
        logging.info(f'Solver failed: {sr.extra}')
        return Result(
            scent=solver.scent(), status='FAIL', score=None, solution=None,
            extra=dict(solver=sr.extra, solver_time=solver_time))
    elif isinstance(sr.data, str):
        logging.info('Checking with validator...')
        start = time.time()
        er = validate.run(task_data, sr.data)
        validator_time = time.time() - start
        logging.info(f'It took {validator_time}')

        if er.time is None:
            logging.info(f'Check failed: {er.extra}')
            return Result(
                scent=solver.scent(), status='CHECK_FAIL', score=None, solution=sr.data,
                extra=dict(
                    solver=sr.extra, validator=er.extra,
                    expected_score=sr.expected_score,
                    solver_time=solver_time, validator_time=validator_time))
        else:
            logging.info(f'Solution verified, score={er.time}')
            # TODO: warn if score != expected_score
            return Result(
                scent=solver.scent(), status='DONE', score=er.time, solution=sr.data,
                extra=dict(
                    solver=sr.extra, validator=er.extra,
                    expected_score=sr.expected_score,
                    solver_time=solver_time, validator_time=validator_time))
    else:
        assert False, sr.data


@dataclass
class InputEntry:
    solver: interface.Solver
    task_id: int
    task_name: str  # like 'prob-042'
    task_data: str


@dataclass
class OutputEntry:
    worker_index: int
    task_id: int
    result: Result


def work(
        index,
        log_path,
        input_queue: multiprocessing.queues.SimpleQueue,
        output_queue: multiprocessing.queues.SimpleQueue):
    logging.basicConfig(
        filename=log_path,
        filemode='w',
        level=logging.INFO,
        format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
    while True:
        input_entry = input_queue.get()
        if input_entry is None:
            logging.info('No more tasks.')
            break
        logging.info(f'Solving task/{input_entry.task_id}...')
        result = solve(input_entry.solver, input_entry.task_data)
        logging.info(f'Done, score={result.score}')
        output_entry = OutputEntry(
            worker_index=index,
            task_id=input_entry.task_id,
            result=result)
        output_queue.put(output_entry)


def parse_args():
    cores = max(multiprocessing.cpu_count() - 1, 1)
    parser = argparse.ArgumentParser(prog='python -m production.solver_worker')
    # optional
    parser.add_argument('-j', '--jobs', metavar='N', help=f'number of worker threads (default: all {cores} cores)',
            type=int, default=cores)
    parser.add_argument('-n', '--dry-run', help='Do not submit solutions to the database',
            action='store_true')
    # positional
    parser.add_argument('solver', help='solver to use', choices=ALL_SOLVERS.keys())
    parser.add_argument('solver_args', metavar='ARG', help='argument for the solver', nargs='*')
    return parser.parse_args()


def main():
    args = parse_args()

    conn = db.get_conn()
    cur = conn.cursor()

    solver = ALL_SOLVERS[args.solver](args.solver_args)
    logger.info(f'Solver scent: {solver.scent()!r}')

    # Select tasks that don't have solutions with our scent.
    cur.execute('''
        SELECT tasks.id
        FROM tasks
        LEFT OUTER JOIN (
            SELECT task_id AS solution_task_id FROM solutions WHERE scent = %s
        ) AS my_solutions
        ON solution_task_id = tasks.id
        WHERE solution_task_id IS NULL
        ''', [solver.scent()])

    task_ids = [id for [id] in cur]
    logging.info(f'{len(task_ids)} tasks to solve: {task_ids}')

    # to reduce collisions when multiple solvers are working in parallel
    random.shuffle(task_ids)
    # task_ids.sort(reverse=True)

    num_workers = args.jobs
    output_queue = multiprocessing.SimpleQueue()
    input_queues = [multiprocessing.SimpleQueue() for _ in range(num_workers)]
    workers = []
    for i, iq in enumerate(input_queues):
        log_path = utils.project_root() / 'outputs' / f'solver_worker_{i:02}.log'
        logging.info(f'Worker logging to {log_path}')
        w = multiprocessing.Process(target=work, args=(i, log_path, iq, output_queue))
        w.start()
    available_workers = set(range(num_workers))

    cur = conn.cursor()
    while True:
        if available_workers and task_ids:
            task_id = task_ids.pop()
            cur.execute(
                'SELECT COUNT(*) FROM solutions WHERE task_id = %s AND scent = %s',
                [task_id, solver.scent()])
            [num_attempts] = cur.fetchone()
            if num_attempts == 0:
                cur.execute(
                    'SELECT name, data FROM tasks WHERE id = %s',
                    [task_id])
                [task_name, task_data] = cur.fetchone()
                task_data = zlib.decompress(task_data).decode()
                worker_index = available_workers.pop()
                input_queues[worker_index].put(InputEntry(
                    solver=solver,
                    task_id=task_id,
                    task_name=task_name,
                    task_data=task_data))
                logging.info(f'task/{task_id} goes to worker {worker_index}')
            else:
                logging.info(f'task/{task_id} already done by another worker, skipping')
            logging.info(f'{len(task_ids)} tasks remaining')
        else:
            if len(available_workers) == num_workers:
                break
            # TODO: keep invocation alive
            output_entry = output_queue.get()
            assert output_entry.worker_index not in available_workers
            available_workers.add(output_entry.worker_index)
            logging.info(
                f'Got solution for task/{output_entry.task_id}, '
                f'score={output_entry.result.score} '
                f'from worker {output_entry.worker_index}')
            if args.dry_run:
                logging.info(f'Skip saving because dry-run')
            else:
                put_solution(conn, output_entry.task_id, output_entry.result)
                conn.commit()

    logging.info('All done, joining workers...')
    for iq in input_queues:
        iq.put(None)
    for w in workers:
        join()


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
