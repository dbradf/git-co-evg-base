# git-co-evg-base Documentation

Find and checkout a recent git commit that matches the specified criteria.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/git-co-evg-base) [![PyPI](https://img.shields.io/pypi/v/git-co-evg-base.svg)](https://pypi.org/project/git-co-evg-base/) [![Upload Python Package](https://github.com/dbradf/git-co-evg-base/actions/workflows/deploy.yml/badge.svg)](https://github.com/dbradf/git-co-evg-base/actions/workflows/deploy.yml) [![test-python-project](https://github.com/dbradf/git-co-evg-base/actions/workflows/test.yml/badge.svg)](https://github.com/dbradf/git-co-evg-base/actions/workflows/test.yml)

When running an Evergreen patch build, it can be useful that base your
changes on a commit in which the tests in Evergreen have already been run.
This way if you encounter any failures in your patch build, you can easily
compare the failure with what was seen in the base commit to understand if
your changes may have introduced the failure.

This command allows you to specify criteria to use to find and checkout a
git commit to start work from.
