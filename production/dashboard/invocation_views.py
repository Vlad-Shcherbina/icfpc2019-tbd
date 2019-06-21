import json
from collections import defaultdict

import flask

from production.dashboard import app, get_conn
from production.dashboard.flask_utils import memoized_render_template_string


@app.template_filter('json_dump')
def json_dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False)


@app.template_filter('render_version')
def render_version(version):
    return flask.Markup(memoized_render_template_string('''\
    <a href="https://github.com/Vlad-Shcherbina/icfpc2019-tbd/commit/{{
        version['commit'] }}">
        {{ version['commit'][:8] -}}
    </a>
    (#{{ version['commit_number'] }})
    {% if version['diff_stat'] %}
        <u><span title="{{ version['diff_stat'] }}">dirty</span></u>
    {% endif %}
    ''', **locals()))


@app.route('/invs')
def list_invocations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    SELECT
        id,
        CASE
            WHEN status = 'RUN' AND update_time < NOW() THEN 'LOST'
            ELSE status
        END,
        start_time,
        update_time,
        data
    FROM invocations
    ''')
    rows = list(cur)
    def key(row):
        status = row[1]
        start_time = row[2]
        end_time = row[3]
        if status == 'RUN':
            return 2, start_time
        else:
            return 1, end_time
    rows.sort(key=key, reverse=True)

    t = type
    return memoized_render_template_string(LIST_INVOCATIONS_TEMPLATE, **locals())

LIST_INVOCATIONS_TEMPLATE = '''\
{% extends "base.html" %}
{% block body %}
<h3>All invocations</h3>
<table>
    <tr>
        <th></th>
        <th>Command</th>
        <th>Version</th>
        <th>User</th>
        <th>Start time</th>
        <th>Status</th>
        <th>End time</th>
    </tr>
{% for id, status, start_time, end_time, inv in rows %}
    <tr>
        <td>{{ url_for('view_invocation', id=id) | linkify }}</td>
        <td>{{ inv['argv'] | join(' ') }}</td>
        <td>{{ inv['version'] | render_version }}</td>
        <td>{{ inv['user'] }}</td>
        <td>{{ start_time.strftime('%m-%d %H:%M:%S') }}</td>
        <td>{{ status }}</td>
        <td>
            {% if status != 'RUN' %}
                {{ end_time.strftime('%m-%d %H:%M:%S') }}
            {% endif %}
        </td>
    </tr>
{% endfor %}
</table>
{% endblock %}
'''


@app.route('/inv/<int:id>')
def view_invocation(id):
    return 'TODO'
