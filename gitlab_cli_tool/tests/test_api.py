import os
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
)


def test_parser_names():
    parsed_args = GitLabCLI.parse_args(CORRECT_CLI_ARGUMENTS)
    assert parsed_args.property_name == 'runners'
    assert parsed_args.action ==['list']
    assert parsed_args.tag == ['atf']


def test_checking_filters():
    cli = GitLabCLI()
    cli.assign_args_to_cli(WRONG_CLI_ARGUMENTS)
    assert False is cli.check_filters()
    cli.assign_args_to_cli(CORRECT_CLI_ARGUMENTS)
    assert True is cli.check_filters()


def test_check_gitlabdatafilter_init():
    cli = GitLabCLI()
    cli.assign_args_to_cli(CORRECT_CLI_ARGUMENTS)
    cli_filter = GitLabDataFilter(property_name=cli.property_name, action=cli.action, tags=cli.tags,
                                  names=cli.names)
    assert cli.property_name == cli_filter.property_name
    assert cli.action == cli_filter.action
    assert cli.tags == cli_filter.tags
    assert cli.names == cli_filter.names


def test_get_projects_filtered_runners_by_tags(gitlabapi, project_runners_dict):
    tags1 = ['tag1']
    expected_output1 = project_runners_dict[:6]
    tags2 = ['tag']
    expected_output2 = project_runners_dict
    tags3 = ['tag3']
    expected_output3 = project_runners_dict[6:]
    output = gitlabapi.get_projects_filtered_runners_by_tags(project_runners_dict, tags1)
    assert expected_output1 == output
    output = gitlabapi.get_projects_filtered_runners_by_tags(project_runners_dict, tags2)
    assert expected_output2 == output
    output = gitlabapi.get_projects_filtered_runners_by_tags(project_runners_dict, tags3)
    assert expected_output3 == output


def test_filter_by_names(gitlabapi, project_runners_with_names):
    names_filters = ['qa-01', 'qa-02']
    correct_output = [1, 2, 3]
    output = gitlabapi.filter_by_names(project_runners_with_names, names_filters)
    assert correct_output == output


@mock.patch('gitlab_cli_tool.cli_api.GitlabAPI.filter_by_names')
@mock.patch('gitlab_cli_tool.cli_api.GitlabAPI.get_projects_runners')
def test_get_projects_filtered_runners_by_names(mock_project_runners, mock_filter_by_name, gitlabapi, project_runners):
    mock_project_runners.return_value = project_runners
    mock_filter_by_name.return_value = FILTERED_BY_NAME
    correct_output = FILTERED_BY_NAME
    output = gitlabapi.get_projects_filtered_runners_by_name(1, 1)
    output = [runner.id for runner in output]
    assert sorted(correct_output) == sorted(output)


@responses.activate
def test_handle_pagination(gitlabapi):
    responses.add(
        responses.Response(
            method='GET',
            url=URLS_FOR_PAGINATION[0],
            json=[{'id': '1'}],
            headers=HEADERS_FOR_PAGINATION[0]
        )
    )
    responses.add(
        responses.Response(
            method='GET',
            url=URLS_FOR_PAGINATION[1],
            json=[{"id": '2'}],
            headers=HEADERS_FOR_PAGINATION[1]
        )
    )
    responses.add(
        responses.Response(
            method='GET',
            url=URLS_FOR_PAGINATION[2],
            json=[{"id": '3'}],
            headers=HEADERS_FOR_PAGINATION[2]
        )
    )
    output = gitlabapi.handle_pagination(URLS_FOR_PAGINATION[0])
    expected_output = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
    assert output == expected_output


def test_count_jobs_for_runners():
    output = GitlabAPI.count_jobs_for_runners(JOBS_WITH_RUNNERS)
    expected_output = {278: 2, 279: 1, 280: 2}
    assert output == expected_output


@mock.patch('gitlab_cli_tool.cli_api.GitlabAPI.count_jobs_for_runners')
@mock.patch('gitlab_cli_tool.cli_api.GitlabAPI.get_running_jobs_from_project')
def test_assign_active_jobs_to_runners(running_jobs_from_project, counted_jobs_for_runners, gitlabapi):
    running_jobs_from_project.return_value = mock.Mock()
    counted_jobs_for_runners.return_value = {278: 2, 279: 1, 280: 2}
    expected_output = [{'id': 278, 'active_jobs': 2}, {'id': 279, 'active_jobs': 1}, {'id': 280, 'active_jobs': 2},
                       {'id': 281, 'active_jobs': 0}]
    output = gitlabapi.assign_active_jobs_to_runners(RUNNERS, 1)
    assert output == expected_output


def test_format_variables(gitlabapi):
    variables = ["var1=1", "var2=2"]
    expected_output = {'var1': '1', 'var2': '2'}
    output = gitlabapi.format_variables(variables)
    assert output == expected_output


# todo Update this test
# @mock.patch('gitlab_cli_tool.cli_api.GitLabDataFilter.check_filters')
# def test_get_filtered_data_WRONG(mock_check_filters, gitlabdatafilter):
#     mock_check_filters.return_value = Filtering.WRONG
#     output = gitlabdatafilter.get_filtered_data()
#     expected_output = 'Wrong arguments'
#     assert output == expected_output

# todo Update this test
# @mock.patch('gitlab_cli_tool.cli_api.GitlabAPI.run_pipeline')
# @mock.patch('gitlab_cli_tool.cli_api.GitLabDataFilter.check_filters')
# def test_get_filtered_data_RUN_PIPELINE(mock_check_filters, mock_run_pipeline, gitlabdatafilter):
#     mock_check_filters.return_value = Filtering.RUN_PIPELINE
#     mock_run_pipeline.return_value = 'www.test.com'
#     output = gitlabdatafilter.get_filtered_data()
#     expected_output = 'www.test.com'
#     assert mock_run_pipeline.call_count == 1
#     mock_run_pipeline.assert_called_with('dummy', 1, 'dummy')  # 1 is the project_id which will change later
#     assert expected_output == output

# todo Update this test
# @mock.patch('gitlab_cli_tool.cli_api.GitLabDataFilter.format_output')
# @mock.patch('gitlab_cli_tool.cli_api.GitLabDataFilter.check_filters')
# def test_get_filtered_data_parameters(mock_check_filters, mock_format_output, gitlabdatafilter_with_api):
#     filters_to_check = [Filtering.LIST, Filtering.LIST_TAGS, Filtering.LIST_NAMES, Filtering.PAUSE_TAGS,
#                         Filtering.PAUSE_NAMES, Filtering.RESUME_TAGS, Filtering.RESUME_NAMES]
#     for filter_to_check in filters_to_check:
#         mock_check_filters.return_value = filter_to_check
#         mock_format_output.return_value = "Check"
#         output = gitlabdatafilter_with_api.get_filtered_data()
#         assert output == "Check"


def test_wrong_variables():
    cli = GitLabCLI()
    cli.variables = ["WrongVariable"]
    with pytest.raises(RuntimeError) as raise_info:
        cli.check_filters()
    assert "Variables passed have wrong format." in str(raise_info.value)


def test_convert_secrets_to_dict(gitlabdatafilter):
    secrets = ["SERVER=dummy", "TOKEN=dummy", "TRIGGER_TOKEN=dummy"]
    expected_output = {"SERVER": "dummy", "TOKEN": "dummy", "TRIGGER_TOKEN": "dummy"}
    output = gitlabdatafilter.convert_secrets_to_dict(secrets)
    assert output == expected_output
    wrong_secrets = ["SERVERxdummy", "TOKENxdummy", "TRIGGER_TOKEN=dummy"]
    output = gitlabdatafilter.convert_secrets_to_dict(wrong_secrets)
    assert {} == output


@mock.patch('os.path.expanduser')
@mock.patch('os.makedirs')
@mock.patch('gitlab_cli_tool.cli_api.GitLabDataFilter.assign_secrets_to_class')
@mock.patch('builtins.open',
            new_callable=mock.mock_open(read_data="SERVER=server"))
@mock.patch('os.path.exists')
def test_assign_secrets(os_path_exists_mock, open_mock, assign_secrets_to_class_mock, os_makedirs_mock, expanduser_mock,
                        gitlabdatafilter):
    file_content = "SERVER=server_name\nTOKEN=token\nTRIGGER_TOKEN=trigger_token\nPROJECT_ID=1\n"
    os_path_exists_mock.return_value = True
    expanduser_mock.return_value = ''
    gitlabdatafilter.assign_secrets()
    open_mock.assert_called_with('/secrets.txt', 'r')
    assert os_makedirs_mock.call_count == 0
    assert assign_secrets_to_class_mock.call_count == 1
    # checking if assign_secrets_to_class was called with changed read_data argument (SERVER=server)
    # for dictionary {"SERVER":'server'}
    assert assign_secrets_to_class_mock.called_with({"SERVER": 'server'})

    os_path_exists_mock.return_value = False
    gitlabdatafilter.assign_secrets()
    assert os_makedirs_mock.call_count == 1
    assert assign_secrets_to_class_mock.call_count == 2
    assert call().__enter__().write(file_content) in open_mock.mock_calls


@mock.patch('gitlab_cli_tool.cli_api.Gitlab')
@mock.patch('os.path.expanduser')
def test_assign_secrets_temporary_file_no_exist(expanduser_mock, gitlab_mock):
    expected_output = ['SERVER=server_name', 'TOKEN=token', 'TRIGGER_TOKEN=trigger_token', 'PROJECT_ID=1']
    with tempfile.TemporaryDirectory() as tmpdirname:
        expanduser_mock.return_value = tmpdirname
        gitlab_filter = GitLabDataFilter()
        assert os.path.exists(f'{tmpdirname}/secrets.txt')
        with open(f'{tmpdirname}/secrets.txt', "r") as f:
            secrets = f.read().splitlines()
        assert expected_output == secrets
        assert gitlab_filter.server == 'server_name'
        assert gitlab_filter.token == 'token'
        assert gitlab_filter.trigger_token == 'trigger_token'


@mock.patch('gitlab_cli_tool.cli_api.Gitlab')
@mock.patch('os.path.expanduser')
def test_assign_secrets_temporary_file_exists(expanduser_mock, gitlab_mock):
    with tempfile.TemporaryDirectory() as tmpdirname:
        expanduser_mock.return_value = tmpdirname
        os.makedirs(os.path.dirname(f'{tmpdirname}/secrets.txt'), exist_ok=True)
        with open(f'{tmpdirname}/secrets.txt', "w") as f:
            f.write(
                "SERVER=test_server\nTOKEN=test_token\nTRIGGER_TOKEN=test_trigger_token\nPROJECT_ID=1\n")
        assert os.path.exists(f'{tmpdirname}/secrets.txt')
        gitlab_filter = GitLabDataFilter()
        assert gitlab_filter.server == 'test_server'
        assert gitlab_filter.token == 'test_token'
        assert gitlab_filter.trigger_token == 'test_trigger_token'
