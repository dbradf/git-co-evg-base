---
weight: 3
---
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

{{< hint warning >}}
**Note**: 
All actions except **none** will perform a `git fetch origin` to ensure the found revision
is available locally.
{{< /hint >}}

For the **rebase** and **merge** operations, if any merge conflicts occur, they will be reported and
the repository will be left in the unmerged state for manually resolution.

For the **checkout** option, you can specify a branch name to create on checkout with the `-b` or
`--branch` option.

For example, to create a branch named `my-branch`, use the following:

```bash
git co-evg-base --git-operation checkout --branch my-branch
```

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
