---
weight: 2
---
## Evergreen authentication

This tool needs to talk to evergreen via the evergreen api in order to function. If you have setup
the evergreen command line tool as described [here](https://github.com/evergreen-ci/evergreen/wiki/Using-the-Command-Line-Tool#downloading-the-command-line-tool),
everything should be setup for the tool to function.

If for some reason the `.evergreen.yml` file that contains your username and api key is not in your
home directory, you will need to use the `--evg-config-file` option to specify the location when 
running the command.
