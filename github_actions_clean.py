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
    parser = argparse.ArgumentParser(description='github_actions_clean.py - clean github action logs and artifacts')
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
    if  username and token:
        auth = (username, token)
    else:
        print('authentication incomplete (either user or token are missing)')
        sys.exit(0)

    return (debug, auth, reponame, branchlist, commit_num)

def branchlist_get(debug, auth, reponame):
    """ get list of branches from github """
    print_debug(debug, 'branchlist_get()')
    branch_list = []
    url = 'https://api.github.com/repos/{0}/branches'.format(reponame)
    resp = requests.get(url=url, auth=auth)
    for branch in resp.json():
        if 'name' in branch:
            branch_list.append(branch['name'])

    return branch_list

def actionslist_get(debug, auth, reponame):
    """ get list of runs """
    print_debug(debug, 'actionslist_get()')
    perpage = 100
    url = 'https://api.github.com/repos/{0}/actions/runs?per_page={1}'.format(reponame, perpage)
    resp = requests.get(url=url, auth=auth)

    pagenum = 0
    if 'total_count' in resp.json():
        pagenum = math.ceil(resp.json()['total_count']/perpage)
        print_debug(debug, 'totalcount: {0}, perpage: {1}, pages: {2}'.format(resp.json()['total_count'], perpage, pagenum))

    workflow_list = []
    if pagenum:
        for ele in range(1, pagenum+1):
            print_debug(debug, 'fetching page: {0}'.format(ele))
            url = 'https://api.github.com/repos/{0}/actions/runs?per_page={1}&page={2}'.format(reponame, perpage, ele)
            resp = requests.get(url=url, auth=auth)
            if 'workflow_runs' in resp.json():
                workflow_list.extend(resp.json()['workflow_runs'])

    # json_store('ids.json', workflow_list)
    return workflow_list

def actionlist_group(debug, action_list):
    """ group action list by branch """
    print_debug(debug, 'actionlist_group()')
    actions_dic = {}
    for workflow in action_list:
        if 'head_branch' in workflow and 'head_sha' in workflow and 'head_commit' in workflow and 'id' in workflow:
            uts = int(calendar.timegm(parse(workflow['head_commit']['timestamp']).timetuple()))
            # print(workflow['id'], workflow['head_branch'], workflow['head_sha'], workflow['head_commit']['timestamp'], uts)

            # add branchname to dictionary
            if workflow['head_branch'] not in actions_dic:
                actions_dic[workflow['head_branch']] = {}

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
        print('{0}: {1}'.format(datetime.now(), text))

def idlist_filter(debug, action_dic, branch_list, commit_number):
    """ select ids to be deleted """
    print_debug(debug, 'idlist_filter({0})'.format(commit_number))
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
    print_debug(debug, 'idlist_delete({0})'.format(len(id_list)))
    for id_ in id_list:
        print_debug(debug, 'delete id: {0}'.format(id_))
        url = 'https://api.github.com/repos/{0}/actions/runs/{1}'.format(reponame, id_)
        resp = requests.delete(url=url, auth=auth)

if __name__ == '__main__':

    (DEBUG, AUTH, REPONAME, BRANCHLIST, COMMIT_NUMBER) = arg_parse()

    if not BRANCHLIST:
        BRANCH_LIST = branchlist_get(DEBUG, AUTH, REPONAME)
    # print(BRANCH_LIST)
    if BRANCH_LIST:
        ACTION_LIST = actionslist_get(DEBUG, AUTH, REPONAME)
    # ACTION_LIST = json_load('foo.json')

    # group actions per branch
    ACTION_DIC = actionlist_group(DEBUG, ACTION_LIST)

    # select ids to be deleted
    ID_LIST = idlist_filter(DEBUG, ACTION_DIC, BRANCH_LIST, COMMIT_NUMBER)

    idlist_delete(DEBUG, AUTH, REPONAME, ID_LIST)
