import logging
logger = logging.getLogger(__name__)
import json
import zlib
from zipfile import ZipFile
import re

from production import db
from production import utils


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    conn = db.get_conn()
    cur = conn.cursor()

    legends = {}
    for part_number, part_name in (1, 'initial'), (2, 'teleports'), (3, 'clones'):
        with ZipFile(utils.project_root() / 'tasks' / f'part-{part_number}-{part_name}.zip') as z:
            with z.open(f'part-{part_number}-legend.txt') as fin:
                for line in fin:
                    name, legend = line.decode().split(' - ', maxsplit=1)
                    legends[name] = legend.rstrip()

            for filename in z.namelist():
                if filename.endswith('-legend.txt'):
                    continue
                m = re.match(r'(prob-\d{3}).desc$', filename)
                assert m, filename
                name = m.group(1)

                with z.open(filename, 'r') as fin:
                    task = fin.read().decode()

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
