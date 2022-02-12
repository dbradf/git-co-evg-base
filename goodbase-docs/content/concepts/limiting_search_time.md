---
weight: 6
---
The tool will limit how far back it will search before giving up. By default, it will look back
50 commits. This can be customized, however. There are three ways to limit how far back is searched:

* **commit** [default=50]: The `--commit-lookback` option takes an argument that specifies how many
  commits to search before giving up.
* **time**: The `--timeout-secs` option takes an argument that specifies how many seconds to search 
  before giving up. By default, there is no limit.
* **specific commit**: The `--commit-limit` option takes an git commit hash for an argument once 
  that commit is found, searching will stop. 

### Examples

Only look at the most recent 100 commits:

```bash
git co-evg-base --commit-lookback 100
```

Limit search to 1 minute:

```bash
git co-evg-base --timeout-secs 60
```

Only look back until commit 'abc123' is found:

```bash
git co-evg-base --commit-limit abc123
```

Search until any of the above limits are hit:

```bash
git co-evg-base --commit-lookback 100 --timeout-secs 60 --commit-limit abc123
```
