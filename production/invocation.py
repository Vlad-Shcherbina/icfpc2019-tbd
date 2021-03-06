import sys
import os
import getpass
import subprocess
import platform

def get_this_invocation():
    argv = sys.argv[:]
    argv[0] = os.path.relpath(argv[0])

    result = dict(
        version=get_version(),
        argv=argv,
        user=f"{getpass.getuser()}@{platform.node()}",
    )
    return result


def get_version():
     # to refresh diff cache
    subprocess.check_output('git status', shell=True)
    diff_stat = subprocess.check_output(
        f'git diff HEAD --stat',
        shell=True, universal_newlines=True)
    commit = subprocess.check_output(
        'git rev-parse HEAD',
        shell=True, universal_newlines=True).strip()
    commit_number = int(subprocess.check_output(
        'git rev-list --count HEAD',
        shell=True, universal_newlines=True))
    return dict(
        commit=commit,
        commit_number=commit_number,
        diff_stat=diff_stat)


if __name__ == '__main__':
    from pprint import pprint
    pprint(get_this_invocation())
