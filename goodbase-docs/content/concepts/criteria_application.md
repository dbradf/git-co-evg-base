---
weight: 2
---
## Applying checks to build variants

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
