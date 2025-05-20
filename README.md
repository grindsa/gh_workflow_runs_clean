<!-- markdownlint-disable  MD013 -->
# gh_workflow_runs_delete.py

`gh_workflow_runs_delete.py` is a small python script helping you to "mass-delete" Github Actions workflow runs as such a feature isn't available in the webbased Actions UI.

It uses the WorkFlow Runs API allowing `delete` operations by using the `/repos/{owner}/{repo}/actions/runs` endpoint.

By default the script scans a repository to get a list of branches and deletes all workflow runs except the ones belonging to the latest commit per branch. The list of branches as well as the amount of commits to be kept can be adjusted.

## Pre-requisites

You need a personal access token with the following permissions:

- repo
- workflow
- read:org

## Installation

- download and unpack the archive
- install dependencies

```bash
> pip install -r requirements.txt
```

## Usage

```bash
python3 ./gh_workflow_runs_delete.py -r {owner}/{repo} -t {TOKEN} -u {github_user}
```

Below the list of command line options

```bash
py gh_actions_clean> py .\gh_workflow_runs_delete.py -h

usage: gh_workflow_runs_delete.py [-h] [-d] [-r REPONAME] [-u USERNAME] [-t TOKEN] [-c COMMITS]
                                  [--branchlist BRANCHLIST]

gh_workflow_runs_delete.py - delete github action logs and artifacts

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           debug mode
  -r REPONAME, --reponame REPONAME
                        repositoryname
  -u USERNAME, --username USERNAME
                        username
  -t TOKEN, --token TOKEN
                        token
  -c COMMITS, --commits COMMITS
                        number of commits to keep
  --branchlist BRANCHLIST
                        list of branches
```

## Usage as part of a Github workflow

I created an [example workflow](https://github.com/grindsa/gh_workflow_runs_clean/blob/main/.github/workflows/gha_clean.yml) which is cleaning up my repositories once a week.

```YAML
# workflow to clean github workflow runs for my repositories

name: Github WF Runs Clean
on:
  push:
  schedule:
    # * is a special character in YAML so you have to quote this string
    - cron:  '0 2 * * 6'

jobs:
  gha_clean:
    runs-on: ubuntu-latest
    name: Github WF Runs Clean
    steps:
    - uses: actions/checkout@v2
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: check self
      run: |
        python3 ./gh_workflow_runs_delete.py -d  -r grindsa/github_actions_clean -t ${{ secrets.GH_TOKEN }} -u ${{ secrets.GH_USER }}  -c 1
    - name: check a2c
      run: |
        python3 ./gh_workflow_runs_delete.py -d  -r grindsa/acme2certifier -t ${{ secrets.GH_TOKEN }} -u ${{ secrets.GH_USER }}  -c 1
    - name: check est_proxy
      run: |
        python3 ./gh_workflow_runs_delete.py -d  -r grindsa/est_proxy -t ${{ secrets.GH_TOKEN }} -u ${{ secrets.GH_USER }}  -c 1
    - name: check dkb-robo
      run: |
        python3 ./gh_workflow_runs_delete.py -d  -r grindsa/dkb-robo -t ${{ secrets.GH_TOKEN }} -u ${{ secrets.GH_USER }}  -c 1
    - name: check dkb-robo
      run: |
        python3 ./gh_workflow_runs_delete.py -d  -r grindsa/docker-pen -t ${{ secrets.GH_TOKEN }} -u ${{ secrets.GH_USER }}  -c 1
```

## Contributing

Please read [CONTRIBUTING.md](https://github.com/grindsa/gh_workflow_runs_clean/blob/main/CONTRIBUTING.md) for details on my code of conduct, and the process for submitting pull requests.
Please note that I have a life besides programming. Thus, expect a delay in answering.

## Versioning

I use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/grindsa/gh_workflow_runs_clean/tags).

## License

This project is licensed under the GPLv3 - see the [LICENSE.md](https://github.com/grindsa/gh_workflow_runs_clean/blob/main/LICENSE) file for details
