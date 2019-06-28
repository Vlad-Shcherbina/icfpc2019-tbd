import logging
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
logger = logging.getLogger(__name__)

from math import log, inf
from datetime import datetime

import matplotlib.pyplot as plt

from production import db
from production import utils


def main():
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, stats FROM tasks WHERE name LIKE 'prob-%'")
    stats_by_task_id = dict(cur)

    cur.execute('''
    SELECT
        tasks.id, solutions.scent, solutions.score, solutions.time
    FROM solutions
    JOIN tasks
    ON solutions.task_id = tasks.id
    WHERE
        tasks.name LIKE 'prob-%' AND
        -- solutions.time < TIMESTAMPTZ '2019-06-24 10:00:00+00' AND
        solutions.status = 'DONE'
    ORDER BY solutions.time
    ''')
    rows = list(cur)
    logger.info(f'{len(rows)} solutions')
    scores = {}
    scents = set()
    for task_id, scent, score, time in rows:
        scents.add(scent)
        scores.setdefault(task_id, {})[scent] = score
    num_sol = dict.fromkeys(scents, 0)
    best = dict.fromkeys(scents, 0)
    shared_best = dict.fromkeys(scents, 0)
    for ss in scores.values():
        m = min(ss.values())
        num_min = sum(v == m for v in ss.values())
        for k, v in ss.items():
            num_sol[k] += 1
            if v == m:
                if num_min == 1:
                    best[k] += 1
                else:
                    shared_best[k] += 1

    print('  ,-- #solutions')
    print('  |   ,-- #unique best')
    print('  |   |   ,-- #shared best')
    print('  |   |   |    scent')
    print('  |   |   |     |')
    for scent in sorted(scents):
        if best[scent] or shared_best[scent]:
            print(f'{num_sol[scent]:>3} {best[scent] or "":>3} {shared_best[scent] or "":>3}    {scent}')
    print(sum(best.values()))
    print(sum(shared_best.values()))


    deadline = datetime.fromisoformat('2019-06-24 10:00:00+00:00')
    # print(deadline)
    xs = []
    ys = []
    score_by_task = dict.fromkeys(stats_by_task_id.keys(), inf)
    norm_score_by_task = dict.fromkeys(stats_by_task_id.keys(), 0)
    for task_id, scent, score, time in rows:
        stats = stats_by_task_id[task_id]
        if score < score_by_task[task_id]:
            score_by_task[task_id] = score
            normalized_score = log(stats['width'] * stats['height'], 2) * \
                max(scores[task_id].values()) / score
            norm_score_by_task[task_id] = normalized_score

            xs.append((time - deadline).total_seconds() / 3600)
            ys.append(sum(norm_score_by_task.values()))
    #print(sum(norm_score_by_task.values()))
#    print(xs, ys)
    plt.plot(xs, ys)
    plt.xlabel('time to deadline, hours')
    plt.ylabel('score')
    plt.show()
    # plt.savefig(utils.project_root() / 'outputs/stats.png')


if __name__ == '__main__':
    from importlib.util import find_spec
    if find_spec('hintcheck'):
        import hintcheck
        hintcheck.hintcheck_all_functions()

    main()
