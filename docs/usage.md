# Using git-co-evg-base

## Overview

`git-co-evg-base` is a tool to help find a commit to work from that meets criteria in its
[Evergreen](https://github.com/evergreen-ci/evergreen) build. This help you ensure that certain
tasks are run on your base commit to make sure you have a base to compare your patch results to.

## Criteria

There are 4 types of criteria that can be specified.

* passing tasks
* run tasks
* pass threshold
* run threshold

#### Passing tasks

Passing tasks are tasks that must have completed successfully in Evergreen to meet the criteria.
They are specified with the `--passing-task` option. This option can be specified more than once
to include multiple tasks. 

For example, to ensure I get a revision with the following three tasks passing: `auth`, `auth_audit`,
and `noPassthrough`, I would run the following:

```bash
git co-evg-base --passing-task auth --passing-task auth_audit --passing-task noPassthrough
```

#### Run tasks

Run tasks are similar to passing tasks except they only need to have been executed, they do not 
need to have been successful. This can be useful when working on a fix for a known task failure.
They are specified with the `--run-task` option. This option can be specified more than once
to include multiple tasks.

For example, to ensure I get a revision with the following two tasks run: `jsCore` and `aggregation`,
I would run the following:

```bash
git co-evg-base --run-task jsCore --run-task aggregation
```

#### Pass threshold

Pass threshold ensures that some percentage of tasks in the build variants must have passed to
consider the revision. This can help minimize the number of unrelated failures that might show up
in patch builds. This is specified with the `--pass-threshold` option. 

For example, to ensure that 85% of tasks have passed, I would run the following:

```bash
git co-evg-base --pass-threshold 0.85
```

#### Run threshold

Run threshold is similar to the pass threshold, but tasks only need to have been executed, they do
not need to have been successful.

For example, to ensure that 95% of tasks have been executed, I would run the following:

```bash
git co-evg-base --run-threshold 0.95
```

### Mixing criteria

More than one criteria can be applied at a time. When multiple criteria are specified, all criteria
must be matched in order to consider a revision a match.

For example, the following run would check both the run threshold of an entire build variant and
check that certain tasks pass:

```bash
git co-evg-base --pass-threshold 0.9 --passing-task noPassthrough --passing-task buildscripts_test
```

### Applying checks to build variants

In projects with multiple build variants, you may not desire to apply the criteria to every build
variant. The `--build-variant` option allows you to control which build variants the checks should
apply. The option takes a regular expression as an argument. Any build variants that match against
the regular express will have their criteria checked. 

The `--build-variant` option can be specified multiple times to provide multiple regular expression
to check against.

For example, to check that a task was successful on builds that end with "-required" and "-suggested", 
I would run the following:

```bash
git co-evg-base --passing-task compile_dist_test --build-variant ".*-required" --build-variant ".*-suggested"
```

## Specifying the Evergreen project

By default, the `mongodb-mongo-master` project will be queried. This can be changed by using
the `--evg-project` option.

For example, to query the `mongodb-mongo-v5.0` project, I would run the following:

```bash
git co-evg-base --pass-threshold 0.95 --evg-project mongodb-mongo-v5.0
```

## Performing git actions when the criteria are meet

Once a revision that meets the specified criteria is found, that revision can be used to perform
certain git operations. By default, a git checkout will be performed to checkout the revision
in the local repository. However, the `--git-operation` option can be provided to change this
behavior.

The option takes one of the following as an argument:

* **checkout** [default] - Perform a `git checkout` to checkout the found revision.
* **rebase** - Perform a `git rebase` to rebase changes on top of the found revision.
* **merge** - Perform a `git merge` to merge changes up to the found revision into the current branch.
* **none** - Take no additional actions.

**Note**: All actions except **none** will perform a `git fetch origin` to ensure the found revision
is available locally.

For the **rebase** and **merge** operations, if any merge conflicts occur, they will be reported and
the repository will be left in the unmerged state for manually resolution.

Regardless of the git operation specified, the found revision will always be displayed to the
screen for reference.

### Examples

Find and print a revision that meets the criteria, but perform no actions on the git repository:

```bash
git co-evg-base --pass-threshold 0.85 --git-operation none
```

To rebase my active branch on the most recent commit that meets the threshold:
```bash
git co-evg-base --pass-threshold 0.85 --git-operation rebase
```

## Handling Evergreen modules

Evergreen modules will be handled automatically in projects that use them. When the found revision
is displayed, any modules used in the project will also be displayed along with their git revision
that was used in the Evergreen build.

If any module is locally available in the location specified by the project's evergreen config
file, the git operation performed on the base repository will also be performed on module's
repository. This allows you to ensure that the modules stay in sync with what was run in 
Evergreen.

Example of a repository with modules:

```bash
git co-evg-base --pass-threshold 0.85
Searching mongodb-mongo-master revisions  [------------------------------------]    2%
Found revision: 6fe24f53eb15a29249e3042609c9bd87d5e147ec
        enterprise: 832db4c9f33426d5f95873e5af6916501f6701f9
        wtdevelop: 186281ffe0f77518738647c0a0aae5e0d122ad33
```

## Saving criteria

Instead of typing out the criteria to search for on every execution, criteria can be saved under
a given name and then referenced in future executions.

The `--save-criteria` option will do this. It takes a name to save the criteria under as an 
argument.  When the `--save-criteria` option is specified, the search for a revision will not
occur. The criteria will only be saved.

If `--save-criteria` is run with a previously saved name, there are two possible outcomes. 

(1) If the build variants match the previously specified build variants, the command will fail 
and will need to be re-executed with the `--override` option if you want to overwrite the 
previous criteria.

(2) If the build variants do not match any previous specified build variants, then the criteria
will be added along with existing criteria. This allows you to specify different criteria for
different build variants.

#### Examples

Save a "b-grade" criteria with a pass threshold of 80% on all build variants.

```bash
git co-evg-base --pass-threshold 0.8 --build-variant ".*" --save-criteria b-grade
```

Save a required criteria with a pass threshold of 95% on all required build variants and the 
"compile_dist_test" task passing on the "enterprise-macos" build variant.

```bash
git co-evg-base --pass-threshold 0.95 --build-variant ".*-required" --save-criteria required
git co-evg-base --passing-task compile_dist_test --build-variant "^enterprise-macos$" --save-criteria required
```

### Using saved criteria

Once a criteria has been saved, you can use the `--use-criteria` option to perform a search with 
it. The option takes the name of the saved criteria as an argument

#### Examples

To use the previously saved "required" criteria:

```bash
git co-evg-base --use-criteria required
```

### Seeing previously saved criteria

The `--list-criteria` option can be specified to output the names and rules of all previously
saved criteria.

#### Example

```bash
git co-evg-base --list-criteria
                                  b-grade
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Build Variant Regexes ┃ Success % ┃ Run % ┃ Successful Tasks ┃ Run Tasks ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ .*                    │ 0.8       │       │                  │           │
└───────────────────────┴───────────┴───────┴──────────────────┴───────────┘
                                  required
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Build Variant Regexes ┃ Success % ┃ Run % ┃ Successful Tasks  ┃ Run Tasks ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ .*-required           │ 0.95      │       │                   │           │
├───────────────────────┼───────────┼───────┼───────────────────┼───────────┤
│ ^enterprise-macos$    │           │       │ compile_dist_test │           │
└───────────────────────┴───────────┴───────┴───────────────────┴───────────┘
```

## Specifying how long to search

The tool will limit how far back it will search before giving up. By default, it will look back
50 commits. This can be customized, however. There are two ways to limit how far back is searched:

* **commit** [default=50]: The `--commit-lookback` option takes an argument that specifies how many
  commits to search before giving up.
* **time**: The `--timeout-secs` option takes an argument that specifies how many seconds to search 
  before giving up. By default, there is no limit.

## Getting help

You can get a list of all the available options with the `--help` option. 

**Note**: When using the `--help` option, you will need to call the command directly via `git-co-evg-base`
and not execute it via `git` (i.e. `git co-evg-base`, note the space after `git`). This is due to 
a limitation in the git help system.

Additionally, there is a `--verbose` option that can be specified to get more detailed information 
about what the command is doing.

## Other details

### Evergreen authentication

This tool needs to talk to evergreen via the evergreen api in order to function. If you have setup
the evergreen command line tool as described [here](https://github.com/evergreen-ci/evergreen/wiki/Using-the-Command-Line-Tool#downloading-the-command-line-tool),
everything should be setup for the tool to function.

If for some reason the `.evergreen.yml` file that contains your username and api key is not in your
home directory, you will need to use the `--evg-config-file` option to specify the location when 
running the command.
