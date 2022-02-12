---
weight: 5
---
You can use `--export-criteria` and `--import-criteria` to share criteria rules with others.

### Exporting criteria rules

The `--export-criteria` option will export saved criteria to a file that can be shared. It takes 
the name of a saved criteria as a argument. The option can be specified multiple times to export
multiple named criteria. The `--export-file` is required and takes as an argument that specified
where the exported rules should be written.

#### Examples

Export the previously defined rules:

```bash
git co-evg-base --export-criteria b-grade --export-criteria --export-file criteria.yml
```

### Importing criteria from a file

The `--import-criteria` option will import criteria from a file that previously exported. It takes
the path to the file to import as an argument. If any of the criteria conflict with existing
criteria the command will fail. Use the `--override` option to overwrite these conflicts.

#### Examples

Import rules from an export file:

```bash
git co-evg-base --import-criteria criteria.yml
```

Overwrite existing rules with rules from a export file:

```bash
git co-evg-base --import-criteria criteria.yml --override
```
