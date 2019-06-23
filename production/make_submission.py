import zipfile
import hashlib
import time
import zlib
import re

from production import utils
from production import db


def main():
    t = int(time.time())

    conn = db.get_conn()
    cur = conn.cursor()

    cur.execute('''
        SELECT
            tasks.name, solutions.id, solutions.score, solutions.scent
        FROM tasks
        JOIN solutions ON solutions.task_id = tasks.id
        WHERE solutions.status = 'DONE' AND tasks.name LIKE 'prob-%'
    ''')
    rows = cur.fetchall()
    best_by_task = {}
    for task_name, sol_id, score, scent in rows:
        assert score is not None
        k = (score, sol_id, scent)
        if task_name not in best_by_task:
            best_by_task[task_name] = k
        else:
            if k < best_by_task[task_name]:
                best_by_task[task_name] = k

    print(best_by_task)

    with open(utils.project_root() / 'outputs' / f'submission_{t}.manifest', 'w') as fout:
        for task_name, (score, sol_id, scent) in sorted(best_by_task.items()):
            fout.write(f'{task_name} {score:>15} /sol/{sol_id} by {scent}\n')

    path = (
        utils.project_root() / 'outputs' /
        f'submission_{t}.zip')
    z = zipfile.ZipFile(path, 'w')

    for task_name, (score, sol_id, scent) in sorted(best_by_task.items()):
        print(task_name)
        cur.execute('SELECT data FROM solutions WHERE id = %s', [sol_id])
        [data] = cur.fetchone()
        data = zlib.decompress(data).decode()
        z.writestr(zipfile.ZipInfo(f'{task_name}.sol'), data)

    z.close()

    with open(path, 'rb') as fin:
       h = hashlib.sha256(fin.read()).hexdigest()

    print(f'File:   {path}')
    print(f'SHA256: {h}')


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
