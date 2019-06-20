# Abort test collection on the first failure.
# https://github.com/pytest-dev/pytest/issues/1421#issuecomment-190236599
#
# Without this, if there are C++ compilation errors, pytest will still try
# to import every module independently, and attempt to compile the same broken
# stuff multiple times.

import pytest

def pytest_collectreport(report):
    if report.failed:
        raise pytest.UsageError("Errors during collection, aborting")
