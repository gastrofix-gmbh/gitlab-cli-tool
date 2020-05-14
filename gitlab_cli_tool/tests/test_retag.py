import os
import copy
import tempfile
from unittest import mock
from unittest.mock import call

import pytest
import responses

from gitlab_cli_tool.cli_api import Filtering
from gitlab_cli_tool.cli_api import GitLabDataFilter, GitlabAPI
from gitlab_cli_tool.gitlab_cli import GitLabCLI
from gitlab_cli_tool.tests.conftest import (
    CORRECT_CLI_ARGUMENTS,
    WRONG_CLI_ARGUMENTS,
    JOBS_WITH_RUNNERS,
    RUNNERS,
    URLS_FOR_PAGINATION,
    HEADERS_FOR_PAGINATION,
    FILTERED_BY_NAME,
    ALL_INFO_RUNNERS_DICT
)


def test_filtering_cases(gitlabdatafilter):
    # Filter by name
    expected_runners = [
        {'id': 1, 'description': 'qa-01.01', 'ip_address': '123.12.12.10', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2']},
        {'id': 2, 'description': 'qa-01.02', 'ip_address': '123.12.12.11', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2']}]
    runners = ALL_INFO_RUNNERS_DICT[:]
    filtered_runners = gitlabdatafilter.filter_runners(runners, Filtering.NAMES, ['qa-01'])
    assert expected_runners == filtered_runners
    expected_runners = [
        {'id': 1, 'description': 'qa-01.01', 'ip_address': '123.12.12.10', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2']}]
    runners = ALL_INFO_RUNNERS_DICT[:]
    filtered_runners = gitlabdatafilter.filter_runners(runners, Filtering.NAMES, ['qa-01.01'])
    assert expected_runners == filtered_runners
    expected_runners = []
    runners = ALL_INFO_RUNNERS_DICT[:]
    filtered_runners = gitlabdatafilter.filter_runners(runners, Filtering.NAMES, ['qa-01.0111'])
    assert expected_runners == filtered_runners
    # Filter by tag
    expected_runners = ALL_INFO_RUNNERS_DICT[:]
    runners = ALL_INFO_RUNNERS_DICT[:]
    filtered_runners = gitlabdatafilter.filter_runners(runners, Filtering.TAGS, ['tag-x1'])
    assert expected_runners == filtered_runners
    expected_runners = [{'id': 3, 'description': 'qa-02.01', 'ip_address': '123.12.12.12', 'active': True, 'is_shared': False,
     'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x3']},{'id': 4, 'description': 'qa-02.02', 'ip_address': '123.12.12.13', 'active': True, 'is_shared': False,
     'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2', 'tag-x3']}]
    runners = ALL_INFO_RUNNERS_DICT[:]
    filtered_runners = gitlabdatafilter.filter_runners(runners, Filtering.TAGS, ['tag-x3'])
    assert expected_runners == filtered_runners
    expected_runners = []
    runners = ALL_INFO_RUNNERS_DICT[:]
    filtered_runners = gitlabdatafilter.filter_runners(runners, Filtering.TAGS, ['tag-x4'])
    assert expected_runners == filtered_runners
    expected_runners = ALL_INFO_RUNNERS_DICT[:]
    runners = ALL_INFO_RUNNERS_DICT[:]
    # all tags which have tag inside
    filtered_runners = gitlabdatafilter.filter_runners(runners, Filtering.TAGS, ['tag'])
    assert expected_runners == filtered_runners


def test_ignore_tags(gitlabdatafilter):
    runners = ALL_INFO_RUNNERS_DICT[:]
    expected_runners = [
        {'id': 1, 'description': 'qa-01.01', 'ip_address': '123.12.12.10', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2']},
        {'id': 2, 'description': 'qa-01.02', 'ip_address': '123.12.12.11', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2']}]
    gitlabdatafilter.ignore = ['name', 'qa-02']
    filtered_runners = gitlabdatafilter.ignore_runners(runners)
    assert expected_runners == filtered_runners
    expected_runners = [
        {'id': 3, 'description': 'qa-02.01', 'ip_address': '123.12.12.12', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x3']},
        ]
    gitlabdatafilter.ignore = ['tag', 'tag-x2']
    filtered_runners = gitlabdatafilter.ignore_runners(runners)
    assert expected_runners == filtered_runners



def test_retag_runners(gitlabdatafilter):
    runners = ALL_INFO_RUNNERS_DICT[:]
    tags_to_change = ['tag-x1']
    new_tags = ['tag-TEST']
    runners_after_changes = []
    for runner in runners:
        changed, new_runner = gitlabdatafilter.retag_algorithm(runner, tags_to_change, new_tags)
        runners_after_changes.append(new_runner)
    expected_runners = [
        {'id': 1, 'description': 'qa-01.01', 'ip_address': '123.12.12.10', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-TEST', 'tag-x2']},
        {'id': 2, 'description': 'qa-01.02', 'ip_address': '123.12.12.11', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-TEST', 'tag-x2']},
        {'id': 3, 'description': 'qa-02.01', 'ip_address': '123.12.12.12', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-TEST', 'tag-x3']},
        {'id': 4, 'description': 'qa-02.02', 'ip_address': '123.12.12.13', 'active': True, 'is_shared': False,
         'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-TEST', 'tag-x2', 'tag-x3']}]
    assert expected_runners == runners_after_changes