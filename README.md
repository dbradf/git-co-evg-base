# git-co-evg-base

Find and checkout a recent git commit that matches the specified criteria.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/git-co-evg-base) [![PyPI](https://img.shields.io/pypi/v/git-co-evg-base.svg)](https://pypi.org/project/git-co-evg-base/) 

## Table of contents

1. [Description](#description)
2. [Dependencies](#dependencies)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Contributor's Guide](#contributors-guide)
    - [Setting up a local development environment](#setting-up-a-local-development-environment)
    - [linting/formatting](#lintingformatting)
    - [Running tests](#running-tests)
    - [Automatically running checks on commit](#automatically-running-checks-on-commit)
    - [Versioning](#versioning)
    - [Code Review](#code-review)
    - [Deployment](#deployment)
6. [Resources](#resources)

## Description

When running an Evergreen patch build, it can be useful that base your
changes on a commit in which the tests in Evergreen have already been run.
This way if you encounter any failures in your patch build, you can easily
compare the failure with what was seen in the base commit to understand if
your changes may have introduced the failure.

This command allows you to specify criteria to use to find and checkout a
git commit to start work from.

## Dependencies

* Python 3.8 or later
* git
* [Evergreen config file](https://github.com/evergreen-ci/evergreen/wiki/Using-the-Command-Line-Tool#downloading-the-command-line-tool)

## Installation

We strongly recommend using a tool like [pipx](https://pypa.github.io/pipx/) to install
this tool. This will isolate the dependencies and ensure they don't conflict with other tools.

```bash
$ pipx install git-co-evg-base
```

## Usage

```
Usage: git-co-evg-base [OPTIONS]

  Find and checkout a recent git commit that matches the specified criteria.

  When running an Evergreen patch build, it can be useful that base your
  changes on a commit in which the tests in Evergreen have already been run.
  This way if you encounter any failures in your patch build, you can easily
  compare the failure with what was seen in the base commit to understand if
  your changes may have introduced the failure.

  This command allows you to specify criteria to use to find and checkout a
  git commit to start work from.

  Criteria

  There are 4 criteria that can be specified:

  * The percentage of tasks that have passed in each build. 
  * The percentage of tasks that have run in each build. 
  * Specific tasks that must have passed in each build (if they are part of that build). 
  * Specific tasks that must have run in each build (if they are part of that build).
  
  If not criteria are specified, a success threshold of 0.95 will be used.

  Additionally, you can specify which build variants the criteria should be
  checked against. By default, only builds that end in 'required' will be
  checked.

  Examples

  Working on a fix for a task 'replica_sets' on the build variants
  'enterprise-rhel-80-64-bit' and 'enterprise-windows', to ensure the task has
  been run on those build variants:

      git co-evg-base --run-task replica_sets --build-variant enterprise-rhel-80-64-bit --build-variant --enterprise-windows

  Starting a new change, to ensure that there are no systemic failures on the
  base commit:

      git co-evg-base --pass-threshold 0.98

Options:
  --passing-task TEXT     Specify a task that needs to be passing (can be
                          specified multiple times).
  --run-task TEXT         Specify a task that needs to be run (can be
                          specified multiple times).
  --run-threshold FLOAT   Specify the percentage of tasks that need to be run.
  --pass-threshold FLOAT  Specify the percentage of tasks that need to be
                          successful.
  --evg-config-file PATH  File containing evergreen authentication
                          information.
  --evg-project TEXT      Evergreen project to query against.
  --build-variant TEXT    Build variant to check (can be specified multiple
                          times).
  --help                  Show this message and exit.
```

Checkout using the default criteria:

```bash
$ git co-evg-base
```

Checkout with successful tasks 'auth' and 'auth_audit' on builds 'enterprise-windows' and 
'enterprise-rhel-80-64-bit' and 95% of the tasks are passing.

```bash
$ git co-evg-base --passing-task auth --passing-task auth_audit --run-threshold 0.95 --build-variant enterprise-windows --build-variant enterprise-rhel-80-64-bit
```

## Contributor's Guide

### Setting up a local development environment

This project uses [poetry](https://python-poetry.org/) for setting up a local environment.

```bash
git clone ...
cd ...
poetry install
```

### linting/formatting

This project uses [black](https://black.readthedocs.io/en/stable/) and 
[isort](https://pycqa.github.io/isort/) for formatting.

```bash
poetry run black src tests
poetry run isort src tests
```

### Running tests

This project uses [pytest](https://docs.pytest.org/en/6.2.x/) for testing.

```bash
poetry run pytest
```

### Automatically running checks on commit

This project has [pre-commit](https://pre-commit.com/) configured. Pre-commit will run 
configured checks at git commit time. To enable pre-commit on your local repository run:

```bash
poetry run pre-commit install
```

### Versioning

This project uses [semver](https://semver.org/) for versioning.

Please include a description what is added for each new version in `CHANGELOG.md`.

### Code Review

Please open a Github Pull Request for code review.

### Deployment

Deployment to pypi is automatically triggered on merges to master.

## Resources

* [Evergreen REST documentation](https://github.com/evergreen-ci/evergreen/wiki/REST-V2-Usage)
