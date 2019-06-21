import logging
logger = logging.getLogger(__name__)
import json
import zlib

from production import db
from production import utils


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    conn = db.get_conn()
    cur = conn.cursor()

    legends = {}
    with (utils.project_root() / 'tasks' / 'part-1-initial' / 'part-1-legend.txt').open() as fin:
        for line in fin:
            name, legend = line.split(' - ', maxsplit=1)
            legends[name] = legend.rstrip()

    for n in range(1, 150 + 1):
        name = f'prob-{n:03d}'
        task = utils.get_problem_raw(n)
        data = zlib.compress(task.encode())
        extra = dict(legend=legends[name])

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
            [[task_id]] = res
            logger.info(f'Uploaded {name!r} as /task/{task_id}')
        else:
            logger.info(f'Task {name!r} already exists')

    db.record_this_invocation(conn, status=db.Stopped())
    conn.commit()


if __name__ == '__main__':
    main()
