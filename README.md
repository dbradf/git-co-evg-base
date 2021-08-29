# git-co-evg-base

Find and checkout a recent git commit that matches the specified criteria.

## Table of contents

1. [Description](#description)
2. [Dependencies](#dependencies)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Documentation](#documentation)
6. [Contributor's Guide](#contributors-guide)
    - [Setting up a local development environment](#setting-up-a-local-development-environment)
    - [linting/formatting](#lintingformatting)
    - [Running tests](#running-tests)
    - [Automatically running checks on commit](#automatically-running-checks-on-commit)
    - [Versioning](#versioning)
    - [Code Review](#code-review)
    - [Deployment](#deployment)
7. [Resources](#resources)

## Description

_More detailed description of the project. This descriptions can span
several paragraphs._

## Dependencies

* Python 3.9 or later

## Installation

We strongly recommend using a tool like [pipx](https://pypa.github.io/pipx/) to install
this tool. This will isolate the dependencies and ensure they don't conflict with other tools.

```bash
$ pipx install git-co-evg-base
```

## Usage

_If this is a tool meant to be installed by others include instruction on how to run the
tool, some common usage example, and instructions on how to learn more._

```bash
$ mytool run --with-common-flags
```

```bash
$ mytool --help
This is the usage output.
```

## Documentation

_Links to any additional documentation for the project. This refers to documentation meant
for end users of the project. For APIs, this should include a link to the swagger docs._

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

_Instructions for how to deploy to production. This should include a link to access the deployed
instance in production._

Deployment to production is automatically triggered on merges to master.

## Resources

* [Evergreen REST documentation](https://github.com/evergreen-ci/evergreen/wiki/REST-V2-Usage)
