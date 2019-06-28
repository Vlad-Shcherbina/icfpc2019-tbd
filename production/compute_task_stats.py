import logging
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
logger = logging.getLogger(__name__)

import zlib
import json
import collections

from psycopg2.extras import execute_values

from production.data_formats import *
from production import db
from production import geom


def main():
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute('''
    SELECT id, name, data
    FROM tasks
    ''')
    stats_by_id = {}
    for id, name, data in cur:
        data = zlib.decompress(data).decode()
        task = Task.parse(data)
        bb = geom.poly_bb(task.border)
        boosters = collections.Counter(b.code for b in task.boosters)
        stats = dict(width=bb.x2, height=bb.y2, boosters=dict(boosters))
        logger.info(f'stats for task/{id} {name}: {stats}')
        stats_by_id[id] = json.dumps(stats)

    logger.info('saving stats for all tasks...')
    execute_values(cur, '''
    UPDATE tasks
    SET stats=data.stats::json
    FROM (VALUES %s) AS data(id, stats)
    WHERE tasks.id=data.id
    ''', stats_by_id.items())

    conn.commit()


if __name__ == '__main__':
    main()
