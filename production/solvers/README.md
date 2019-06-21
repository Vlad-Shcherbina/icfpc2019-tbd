### Integrating new solvers

1. Inherit from `Solver` class in [interface.py](https://github.com/Vlad-Shcherbina/icfpc2019-tbd/blob/master/production/solvers/interface.py). Example implementation is in
[greedy.py](https://github.com/Vlad-Shcherbina/icfpc2019-tbd/blob/master/production/solvers/greedy.py)
2. Add your class to [all.py](https://github.com/Vlad-Shcherbina/icfpc2019-tbd/blob/master/production/solvers/all.py).

### Local development

`python -m production.solver_runner <solver> [<solver args>...]`

This command will run your solver on all tasks. Results are printed to the screen but not uploaded to the DB. This is convenient to weed out initial bugs without polluting the DB with too much failed attempts.

Once the solver is more or less ready, move on to `solver_worker`.

### Running solver worker

`python -m production.solver_worker <solver> [<solver args>...]`

It will take all your cores to run specified solver on all available tasks. Solutions and failed attempts will be saved in the DB.
Multiple people can run the same solver at the same time, tasks will be distributed more or less okay.

### Troubleshooting solver_worker

Start [the dashboard](https://github.com/Vlad-Shcherbina/icfpc2019-tbd/blob/master/production/dashboard), find your last invocation in the `/invs` view, open `/inv/<id>` that will list all attempts by your worker, click on individual `/sol/<id>` links. Error messages are preserved there.

### Gathering the solutions

`python -m production.make_submission.py`

It will grab the best solution for every task from the DB, create zip archive and print it's SHA256.
