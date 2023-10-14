#!/usr/bin/python3
""" github action log cleaner """
import argparse
import sys
import math
import calendar
import json
from datetime import datetime
from dateutil.parser import parse
import requests


def arg_parse():
    """ simple argparser """
    parser = argparse.ArgumentParser(description='gh_workflow_runs_delete.py - delete github action logs and artifacts')
    parser.add_argument('-d', '--debug', help='debug mode', action="store_true", default=False)
    parser.add_argument('-r', '--reponame', help='repositoryname', default=None)
    parser.add_argument('-u', '--username', help='username', default=None)
    parser.add_argument('-t', '--token', help='token', default=None)
    parser.add_argument('-c', '--commits', help='number of commits to keep', default=1)
    parser.add_argument('--branchlist', help='list of branches', default=False)
    args = parser.parse_args()

    debug = args.debug
    username = args.username
    token = args.token
    branchlist = args.branchlist
    commit_num = int(args.commits)
    reponame = args.reponame
    auth = None
    if not reponame:
        print('reponame (-r) is missing')
        sys.exit(0)
    if username and token:
        auth = (username, token)
    else:
        print('authentication incomplete (either user or token are missing)')
        sys.exit(0)

    return (debug, auth, reponame, branchlist, commit_num)


def branchlist_get(debug, auth, reponame):
    """ get list of branches from github """
    print_debug(debug, 'branchlist_get()')
    branch_list = ['scheduled']
    url = f'https://api.github.com/repos/{reponame}/branches'
    resp = requests.get(url=url, auth=auth, timeout=20)
    for branch in resp.json():
        if 'name' in branch:
            branch_list.append(branch['name'])

    return branch_list


def wfruns_get(debug, auth, reponame):
    """ get list of runs """
    print_debug(debug, 'wfruns_get()')
    perpage = 100
    url = f'https://api.github.com/repos/{reponame}/actions/runs?per_page={perpage}'
    resp = requests.get(url=url, auth=auth, timeout=20)

    pagenum = 0
    if 'total_count' in resp.json():
        pagenum = math.ceil(resp.json()['total_count'] / perpage)
        print_debug(debug, f'totalcount: {resp.json()["total_count"]}, perpage: {perpage}, pages: {pagenum}')

    workflow_list = []
    if pagenum:
        for ele in range(1, pagenum + 1):
            print_debug(debug, f'fetching page: {ele}')
            url = f'https://api.github.com/repos/{reponame}/actions/runs?per_page={perpage}&page={ele}'
            resp = requests.get(url=url, auth=auth, timeout=20)
            if 'workflow_runs' in resp.json():
                workflow_list.extend(resp.json()['workflow_runs'])

    # json_store('ids.json', workflow_list)
    return workflow_list


def wfruns_group(debug, action_list):
    """ group action list by branch """
    print_debug(debug, 'wfruns_group()')
    actions_dic = {'scheduled': {}}
    for workflow in action_list:
        if 'head_branch' in workflow and 'head_sha' in workflow and 'head_commit' in workflow and 'id' in workflow:
            uts = int(calendar.timegm(parse(workflow['head_commit']['timestamp']).timetuple()))
            # print(workflow['id'], workflow['head_branch'], workflow['head_sha'], workflow['head_commit']['timestamp'], uts)
            # add branchname to dictionary
            if workflow['head_branch'] not in actions_dic:
                actions_dic[workflow['head_branch']] = {}

            if workflow['event'] == 'schedule':
                # special handling for scheduled workflows
                cdate, _junk = workflow['created_at'].split('T', 1)
                if cdate not in actions_dic['scheduled']:
                    actions_dic['scheduled'][cdate] = {'commit': workflow['head_sha'], 'id_list': []}
                actions_dic['scheduled'][cdate]['id_list'].append(workflow['id'])
            else:
                # add uts to branch-tree
                if uts not in actions_dic[workflow['head_branch']]:
                    actions_dic[workflow['head_branch']][uts] = {'commit': workflow['head_sha'], 'id_list': []}
                actions_dic[workflow['head_branch']][uts]['id_list'].append(workflow['id'])

    return actions_dic


def json_load(file_name):
    """ load json structure from file """
    with open(file_name, encoding='utf8') as json_file:
        data = json.load(json_file)
    return data


def json_store(file_name_, data_):
    """ store structure as json to file """
    with open(file_name_, 'w', encoding='utf-8') as out_file:
        json.dump(data_, out_file, ensure_ascii=False, indent=4)


def print_debug(debug, text):
    """ little helper to print debug messages """
    if debug:
        print(f'{datetime.now()}: {text}')


def idlist_filter(debug, action_dic, branch_list, commit_number):
    """ select ids to be deleted """
    print_debug(debug, f'idlist_filter({commit_number})')
    id_list = []
    for branch in action_dic:
        delete = False
        if branch not in branch_list:
            delete = True

        for idx, timestamp in enumerate(sorted(action_dic[branch], reverse=True)):
            if idx >= commit_number:
                # skip latest n commits
                delete = True
            # print_debug(debug, '{0}, {1}, {2}, {3}'.format(branch, timestamp, idx, delete))
            for id_ in action_dic[branch][timestamp]['id_list']:
                if delete:
                    id_list.append(id_)
    return id_list


def idlist_delete(debug, auth, reponame, id_list):
    """ delete worflow logs """
    print_debug(debug, f'idlist_delete({id_list})')
    for id_ in id_list:
        print_debug(debug, f'delete id: {id_}')
        url = f'https://api.github.com/repos/{reponame}/actions/runs/{id_}'
        _resp = requests.delete(url=url, auth=auth, timeout=20)


if __name__ == '__main__':

    (DEBUG, AUTH, REPONAME, BRANCHLIST, COMMIT_NUMBER) = arg_parse()

    if not BRANCHLIST:
        BRANCH_LIST = branchlist_get(DEBUG, AUTH, REPONAME)

    # print(BRANCH_LIST)
    if BRANCH_LIST:
        ACTION_LIST = wfruns_get(DEBUG, AUTH, REPONAME)

    # ACTION_LIST = json_load('foo.json')
    # json_store('wf.json', ACTION_LIST)

    # group actions per branch
    ACTION_DIC = wfruns_group(DEBUG, ACTION_LIST)

    for branch, bdata in ACTION_DIC.items():
        for commit, cdata in bdata.items():
            print_debug(DEBUG, f'{branch} {commit} {len(cdata["id_list"])}')

    # select ids to be deleted
    ID_LIST = idlist_filter(DEBUG, ACTION_DIC, BRANCH_LIST, COMMIT_NUMBER)

    idlist_delete(DEBUG, AUTH, REPONAME, ID_LIST)
