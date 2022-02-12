---
weight: 4
---
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
