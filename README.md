## Setup

CPython 3.7.3 (the latest stable release).

`pip install -r requirements.txt`

Copy `git_hooks/pre-push` to `.git/hooks/`.
Edit it as neccessary to match how you invoke Python in your environment.

You'll need C++ compiler in PATH (on Windows `cl.exe`, on Linux `g++`).


## Running stuff

Root of this repository should be in `PYTHONPATH`, because we use absolute imports (`from production import utils`). There are several ways to achieve that:
  - add project path to the environment variable `PYTHONPATH`
  - create the file `<python installation or venv>/lib/python3.7/site-packages/tbd.pth` whose content is a single line `/path/to/icfpc2019-tbd`
  - configure your favorite IDE appropriately (see below)
  - use `python -m production.some_script` instead of `python production/some_script.py`


## Testing stuff

```
cd icfpc2019-tbd/
pytest
```

There is also
```
cd icfpc2019-tbd/
python -m production.test_all_with_coverage
```


# Random notes

Substitute `pip` with something like `python3.7 -m pip` to ensure that you are using the right version of the interpreter if you have multiple installed. Same for `pytest`.

# Configuring vscode

Sample launch.json:

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "cwd": "${workspaceRoot}",
                "env": {
                    "PYTHONPATH": "${workspaceRoot}"
                }
            }
        ]
    }

Note that python launched from vscode for some reason doesn't have cwd in sys.path so that's why
the env thing is required.

Prevent intellisense from holding onto the extension dlls: settings.json

    {
        "python.jediEnabled": false
    }

(idk how much this decreases the intellisense quality)

As of now: rename "C:\Program Files\Git\usr\bin\link.exe" to "_link.exe".

Because of all this shit I'm currently experimenting with running remote vscode on WSL.