---
weight: 1
---

`git-co-evg-base` allows you to specify criteria that define what a matching evergreen 
version will look like.

There are 4 types of criteria that can be specified.

* passing tasks
* run tasks
* pass threshold
* run threshold

## Passing tasks

Passing tasks are tasks that must have completed successfully in Evergreen to meet the criteria.
They are specified with the `--passing-task` option. This option can be specified more than once
to include multiple tasks. 

For example, to ensure I get a revision with the following three tasks passing: `auth`, `auth_audit`,
and `noPassthrough`, I would run the following:

```bash
git co-evg-base --passing-task auth --passing-task auth_audit --passing-task noPassthrough
```

## Run tasks

Run tasks are similar to passing tasks except they only need to have been executed, they do not 
need to have been successful. This can be useful when working on a fix for a known task failure.
They are specified with the `--run-task` option. This option can be specified more than once
to include multiple tasks.

For example, to ensure I get a revision with the following two tasks run: `jsCore` and `aggregation`,
I would run the following:

```bash
git co-evg-base --run-task jsCore --run-task aggregation
```

## Pass threshold

Pass threshold ensures that some percentage of tasks in the build variants must have passed to
consider the revision. This can help minimize the number of unrelated failures that might show up
in patch builds. This is specified with the `--pass-threshold` option. 

For example, to ensure that 85% of tasks have passed, I would run the following:

```bash
git co-evg-base --pass-threshold 0.85
```

## Run threshold

Run threshold is similar to the pass threshold, but tasks only need to have been executed, they do
not need to have been successful.

For example, to ensure that 95% of tasks have been executed, I would run the following:

```bash
git co-evg-base --run-threshold 0.95
```

## Mixing criteria

More than one criteria can be applied at a time. When multiple criteria are specified, all criteria
must be matched in order to consider a revision a match.

For example, the following run would check both the run threshold of an entire build variant and
check that certain tasks pass:

```bash
git co-evg-base --pass-threshold 0.9 --passing-task noPassthrough --passing-task buildscripts_test
```

