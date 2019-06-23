import json
import zlib
from collections import defaultdict

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
        <td>{{ task_extra.get('legend', '') }}</td>
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


@app.route('/sols')
def list_solutions():
    name_filter = flask.request.args.get('name', '%')

    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            tasks.id, tasks.name,
            solutions.id, solutions.scent, solutions.status, solutions.score,
            solutions.invocation_id, solutions.data IS NOT NULL,
            solutions.extra
        FROM tasks
        LEFT OUTER JOIN solutions ON solutions.task_id = tasks.id
        WHERE tasks.name LIKE %s
        ORDER BY tasks.id ASC, solutions.id DESC
    ''', [name_filter])
    rows = cur.fetchall()
    best_by_task = defaultdict(lambda: float('+inf'))
    for [task_id, _, _, _, _, score, _, _, _] in rows:
        if score is not None:
            best_by_task[task_id] = min(best_by_task[task_id], score)

    return memoized_render_template_string(LIST_SOLUTIONS_TEMPLATE, **locals())

LIST_SOLUTIONS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Solutions</h3>
<table id='t' style="display: none">
{% for task_id, task_name,
       sol_id, sol_scent, sol_status, sol_score, sol_inv_id, sol_has_data, sol_extra in rows %}
    <tr>
        <td>
            {{ ('/task/%s' % task_id) | linkify }}
        </td>
        <td>{{ task_name }}</td>
        {% if sol_id is not none %}
            <td>
                {{ ('/sol/%s' % sol_id) | linkify }}
            </td>
            <td>{{ sol_status }}</td>
            <td>
                {% if best_by_task[task_id] == sol_score %}
                    <b>{{ sol_score }}</b>
                {% else %}
                    {{ sol_score or '' }}
                {% endif %}
            </td>
            <td>
                {% if best_by_task[task_id] == sol_score %}
                    <b>{{ sol_scent }}</b>
                {% else %}
                    {{ sol_scent }}
                {% endif %}
            </td>
            <td>{{ ('/inv/%s' % sol_inv_id) | linkify }}</td>
            <td>
                {{ sol_extra.get('solver_time', 0) | int }}s + {{
                   sol_extra.get('validator_time', 0) | int }}s
            </td>
        {% endif %}
    </tr>
{% endfor %}
</table>

<script src='/static/merge_equal_td.js'></script>
<script>
    let t = document.getElementById('t');
    mergeEqualTd(t, [[0, 1], [6]]);
    t.style.display = "";
</script>

{% endblock %}
'''


@app.route('/sol/<int:id>')
def view_solution(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT task_id, scent, status, score, data, extra, invocation_id '
        'FROM solutions WHERE id = %s',
        [id])
    [task_id, scent, status, score, data, extra, inv_id] = cur.fetchone()
    if data is not None:
        data = zlib.decompress(data)

    return memoized_render_template_string(VIEW_SOLUTION_TEMPLATE, **locals())

VIEW_SOLUTION_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>Solution info</h3>
Status: {{ status }} <br>
Scent: {{ scent }} <br>
Score: {{ score }} <br>
Task: {{ url_for('view_task', id=task_id) | linkify }} <br>
Produced by {{ url_for('view_invocation', id=inv_id) | linkify }} <br><br>
Extra:
<pre>{{ extra | json_dump }}</pre>

{% if extra.get('solver', {}).get('tb') %}
<pre>{{ extra.get('solver', {}).get('tb') }}</pre>
{% endif %}

{% if data %}
<a href="{{ data | data_uri }}" download="sol-{{id}}.sol">download solution</a>
{% endif %}

{% endblock %}
'''
