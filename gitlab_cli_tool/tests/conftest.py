from unittest import mock

import pytest

from gitlab_cli_tool.cli_api import GitlabAPI, GitLabDataFilter

CORRECT_CLI_ARGUMENTS = ['runners', 'list', '--tag', 'atf']
WRONG_CLI_ARGUMENTS = ['runners', 'list', '--tag', 'atf', '--name', 'qa-01.01']
ALL_FILTERED_RUNNERS = [{'id': 261}, {'id': 262}, {'id': 263}, {'id': 264}, {'id': 265}, {'id': 266}, {'id': 267},
                        {'id': 268},
                        {'id': 269}, {'id': 270}, {'id': 271}, {'id': 272}, {'id': 273}, {'id': 274}, {'id': 275},
                        {'id': 276},
                        {'id': 277}, {'id': 278}, {'id': 279}, {'id': 280}, {'id': 281}, {'id': 282}, {'id': 283},
                        {'id': 284},
                        {'id': 285}, {'id': 286}, {'id': 287}, {'id': 288}, {'id': 289}, {'id': 294}]
JOBS_WITH_RUNNERS = [{'job_id': 1, 'runner': {'id': 278}}, {'job_id': 2, 'runner': {'id': 279}},
                     {'job_id': 3, 'runner': {'id': 278}}, {'job_id': 4, 'runner': {'id': 280}},
                     {'job_id': 5, 'runner': {'id': 280}}]
RUNNERS = [{'id': 278}, {'id': 279}, {'id': 280}, {'id': 281}]

FILTERED_BY_NAME = [264, 262, 263]

URLS_FOR_PAGINATION = ['https://gitlab.server.com/api/v4/runners/all?per_page=40',
                       'https://gitlab.server.com/api/v4/runners/all?page=2&per_page=40',
                       'https://gitlab.server.com/api/v4/runners/all?page=3&per_page=40']

HEADERS_FOR_PAGINATION = [{'Content-Type': 'application/json',
                           'Link': '<https://gitlab.server.com/api/v4/runners/all?page=2&per_page=40>; rel="next", <https://gitlab.server.com/api/v4/runners/all?page=1&per_page=40>; rel="first", <https://gitlab.server.com/api/v4/runners/all?page=3&per_page=40>; rel="last"'},
                          {'Content-Type': 'application/json',
                           'Link': '<https://gitlab.server.com/api/v4/runners/all?page=1&per_page=40>; rel="prev", <https://gitlab.server.com/api/v4/runners/all?page=3&per_page=40>; rel="next", <https://gitlab.server.com/api/v4/runners/all?page=1&per_page=40>; rel="first", <https://gitlab.server.com/api/v4/runners/all?page=3&per_page=40>; rel="last"'},
                          {'Content-Type': 'application/json',
                           'Link': '<https://gitlab.server.com/api/v4/runners/all?page=2&per_page=40>; rel="prev", <https://gitlab.server.com/api/v4/runners/all?page=1&per_page=40>; rel="first", <https://gitlab.server.com/api/v4/runners/all?page=3&per_page=40>; rel="last"'}]

ALL_INFO_RUNNERS_DICT = [
    {'id': 1, 'description': 'qa-01.01', 'ip_address': '123.12.12.10', 'active': True, 'is_shared': False,
     'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2']},
    {'id': 2, 'description': 'qa-01.02', 'ip_address': '123.12.12.11', 'active': True, 'is_shared': False,
     'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2']},
    {'id': 3, 'description': 'qa-02.01', 'ip_address': '123.12.12.12', 'active': True, 'is_shared': False,
     'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x3']},
    {'id': 4, 'description': 'qa-02.02', 'ip_address': '123.12.12.13', 'active': True, 'is_shared': False,
     'name': 'gitlab-runner', 'online': True, 'status': 'online', 'tag_list': ['tag-x1', 'tag-x2', 'tag-x3']}]


@pytest.fixture()
def project_runners_with_names():
    project_runners = [1, 2, 3, 4]
    names = ['qa-01.02', 'qa-01.03', 'qa-02.01', 'qa-03.01']
    mock_runners = []
    for project_id, name in zip(project_runners, names):
        mock_runner = mock.Mock()
        mock_runner.id = project_id
        mock_runner.description = name
        mock_runners.append(mock_runner)
    return mock_runners


@pytest.fixture()
def project_runners():
    project_runners = [1, 8, 9, 11, 12, 56, 128, 146, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272]
    mock_runners = []
    for project_id in project_runners:
        mock_runner = mock.Mock()
        mock_runner.id = project_id
        mock_runners.append(mock_runner)
    return mock_runners


@pytest.fixture()
def project_runners_dict():
    project_runners = [1, 8, 9, 11, 12, 56, 128, 146, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272]
    mock_runners = []
    for project_id in project_runners[:6]:
        runner = {'id': project_id, 'tag_list': ['tag1', 'tag2']}
        mock_runners.append(runner)
    for project_id in project_runners[6:]:
        runner = {'id': project_id, 'tag_list': ['tag3']}
        mock_runners.append(runner)
    return mock_runners


@pytest.fixture()
def gitlabapi():
    with mock.patch('gitlab.Gitlab'):
        return GitlabAPI('server', 'token', 'trigger_token')


@pytest.fixture()
def gitlabdatafilter():
    with mock.patch('gitlab_cli_tool.cli_api.Gitlab'):
        return GitLabDataFilter(property_name='dummy', action='dummy', tags='dummy',
                                names='dummy', branch='dummy', variables='dummy')


@pytest.fixture()
def gitlabdatafilter_with_api():
    with mock.patch('gitlab_cli_tool.cli_api.GitlabAPI'):
        return GitLabDataFilter(property_name='dummy', action='dummy', tags='dummy',
                                names='dummy', branch='dummy', variables='dummy')
