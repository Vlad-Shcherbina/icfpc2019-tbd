import logging
logger = logging.getLogger(__name__)
import time
from dataclasses import dataclass
from typing import Union

import psycopg2
import psycopg2.extras

from production.invocation import get_this_invocation


def get_conn():
    logger.info('Connecting to the db...')
    return psycopg2.connect(
        dbname='postgres',
        host='34.77.190.171',
        user='postgres', password='ekcuqaytwfoznoatazstkma')


def create_tables(conn):
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS invocations(
        id SERIAL PRIMARY KEY,

        status TEXT NOT NULL,
        -- 'RUN'
        -- 'STOPPED'

        start_time TIMESTAMP WITH TIME ZONE NOT NULL,

        update_time TIMESTAMP WITH TIME ZONE NOT NULL,
        -- If status is 'STOPPED', termination time.
        -- If status is 'RUN', time to the next planned update.
        -- So if status == 'RUN' and update_time < NOW(),
        -- we can conclude that the invocation terminated abnormally
        -- without notifying the DB.
        -- Let's call it 'LOST' (even though such status will never appear
        -- in the DB explicitly).

        data JSON NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tasks(
        id SERIAL PRIMARY KEY,

        -- like 'prob-042'
        name TEXT NOT NULL UNIQUE,

        -- gzipped task string
        data BYTEA NOT NULL,

        stats JSON NOT NULL,

        obsolete BOOL NOT NULL DEFAULT FALSE,
        -- to mark old Lambda-chain blocks

        extra JSON NOT NULL,

        invocation_id INTEGER NOT NULL REFERENCES invocations,
        time TIMESTAMP WITH TIME ZONE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS solutions(
        id SERIAL PRIMARY KEY,

        status TEXT NOT NULL,
        -- 'DONE' - solution passed the emulator check
        -- 'CHECK_FAIL' - solution was rejected by the emulator
        -- 'FAIL' - solver failed
        -- 'PASS' - solver refused to try this task
        -- These states indicate that the solver failed in a deterministic way.
        -- It will be used to avoid further reruns of the same solver.

        scent TEXT NOT NULL,
        -- Solver will not attempt a problem if there was another attempt
        -- with the same scent.
        -- Use strings like 'My solver 1.0' and bump it when the solver changed
        -- significantly and you want to rerun it on all tasks.

        data BYTEA,
        -- NULL if status = 'FAIL' or 'PASS'

        score BIGINT,
        -- NULL if status != 'DONE'

        extra JSON NOT NULL,
        -- anything that is not the solution: logs, statistics, error messages

        task_id INTEGER NOT NULL REFERENCES tasks,
        invocation_id INTEGER NOT NULL REFERENCES invocations,
        time TIMESTAMP WITH TIME ZONE NOT NULL
    );
    ''')


@dataclass
class KeepRunning:
    update_interval: float  # in seconds
@dataclass
class Stopped:
    pass

_invocation = None
_invocation_id = None

def record_this_invocation(conn, status=Union[KeepRunning, Stopped], **kwargs):
    '''
    Creates or updates entry for current invocation.
    If you pass it status=KeepRunning(42) it means you promise to
    call record_this_invocation() again in no more than 42 seconds.
    kwargs are added to the invocation json.
    '''
    global _invocation, _invocation_id

    if _invocation is None:
        _invocation = get_this_invocation()
    _invocation.update(kwargs)

    if isinstance(status, KeepRunning):
        delta_time = status.update_interval
        status = 'RUN'
    elif isinstance(status, Stopped):
        delta_time = 0
        status = 'STOPPED'
    else:
        assert False, status

    cur = conn.cursor()
    if _invocation_id is None:
        cur.execute(
            '''
            INSERT INTO invocations(start_time, status, update_time, data)
            VALUES(NOW(), %s, NOW() + %s * interval '1 second', %s) RETURNING id
            ''',
            [status, delta_time, psycopg2.extras.Json(_invocation)])
        [_invocation_id] = cur.fetchone()
    else:
        cur.execute(
            '''
            UPDATE invocations SET
                status = %s,
                update_time = NOW() + %s * interval '1 second',
                data = %s
            WHERE id = %s
            ''',
            [status, delta_time, psycopg2.extras.Json(_invocation), _invocation_id])

def get_this_invocation_id(conn) -> int:
    if _invocation_id is None:
        record_this_invocation(conn, status=KeepRunning(60))
    return _invocation_id


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    conn = get_conn()

    create_tables(conn)

    record_this_invocation(conn, status=KeepRunning(30))
    conn.commit()
    logging.info(f'inv/{get_this_invocation_id(conn)} is running...')

    time.sleep(10)

    record_this_invocation(conn, status=Stopped(), comment='hi')
    conn.commit()
    logging.info(f'inv/{get_this_invocation_id(conn)} stopped')


if __name__ == '__main__':
    main()
