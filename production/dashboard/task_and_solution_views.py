import json
import zlib

import flask

from production.dashboard import app, get_conn
from production.dashboard.flask_utils import memoized_render_template_string
from production.data_formats import *
from production.geom import poly_bb, rasterize_poly


@app.route('/tasks')
def list_tasks():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            tasks.invocation_id,
            tasks.id, tasks.name,
            tasks.extra
        FROM tasks
        ORDER BY tasks.id ASC
    ''')
    return memoized_render_template_string(LIST_TASKS_TEMPLATE, **locals())

LIST_TASKS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Tasks</h3>
<table>
{% for task_inv_id, task_id, task_name, task_extra in cur %}
    <tr>
        <td>{{ ('/inv/%s' % task_inv_id) | linkify }}</td>
        <td>{{ ('/task/%s' % task_id) | linkify }}</td>
        <td>{{ task_name }}</td>
        <td>{{ task_extra['legend'] }}</td>
    </tr>
{% endfor %}
</table>
{% endblock %}
'''

@app.route('/task/<int:id>')
def view_task(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            name,
            data,
            extra
        FROM tasks WHERE id = %s''',
        [id])
    [name, data, extra] = cur.fetchone()

    s = zlib.decompress(data).decode()
    task = Task.parse(s)

    bb = poly_bb(task.border)

    grid = [['#'] * (bb.x2 - bb.x1) for y in range(bb.y1, bb.y2)]

    for row in rasterize_poly(task.border):
        for x in range(row.x1, row.x2):
            assert grid[row.y - bb.y1][x - bb.x1] == '#'
            grid[row.y - bb.y1][x - bb.x1] = '.'

    for obstacle in task.obstacles:
        for row in rasterize_poly(obstacle):
            for x in range(row.x1, row.x2):
                assert grid[row.y - bb.y1][x - bb.x1] == '.'
                grid[row.y - bb.y1][x - bb.x1] = '#'

    grid[task.start.y - bb.y1][task.start.x - bb.x1] = '!'

    for booster in task.boosters:
        grid[booster.pos.y - bb.y1][booster.pos.x - bb.x1] = booster.code

    grid = '\n'.join(' '.join(row) for row in reversed(grid))

    return memoized_render_template_string(VIEW_TASK_TEMPLATE, **locals())

VIEW_TASK_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Task info</h3>
Name: {{ name }} <br>
Extra: <pre>{{ extra | json_dump }}</pre>
<pre>
# - wall
. - empty
! - start
BFLX - boosters
</pre>
<pre>{{ grid }}</pre>
{% endblock %}
'''
