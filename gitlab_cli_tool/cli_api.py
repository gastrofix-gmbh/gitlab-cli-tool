import asyncio
import copy
import os
from enum import Enum
from typing import List, Dict, Union

import aiohttp
import requests
from aiohttp.client import ClientSession
from gitlab import Gitlab
from gitlab.v4.objects import ProjectRunner
from tabulate import tabulate


class Filtering(Enum):
    WRONG = 0
    NAMES = 1
    TAGS = 2


class Actions(Enum):
    PAUSE = 'pause'
    RESUME = 'resume'
    LIST = 'list'
    RUN = 'run'
    RETAG = 'retag'


class PropertyName(Enum):
    RUNNERS = 'runners'
    PIPELINE = 'pipeline'
    # TODO implement listing etc for -> PROJECTS = 'projects'


class GitLabDataFilter:
    def __init__(self, **kwargs):
        self.property_name = kwargs.get('property_name')
        self.action = kwargs.get('action')
        self.tags = kwargs.get('tags')
        self.names = kwargs.get('names')
        self.branch = kwargs.get('branch')
        self.variables = kwargs.get('variables')
        self.ignore = kwargs.get('ignore')
        self.server = ''
        self.token = ''
        self.trigger_token = ''
        self.project_id = ''
        self.assign_secrets()
        self.api = GitlabAPI(self.server, self.token, self.trigger_token)

    @staticmethod
    def convert_secrets_to_dict(secrets):
        keys = {}
        for var in secrets:
            try:
                key, value = var.split('=')
                keys[key] = value
            except ValueError:
                print('Wrong format of credentials')
                return {}
        return keys

    def assign_secrets_to_class(self, secrets):
        self.server = secrets['SERVER']
        self.token = secrets['TOKEN']
        self.trigger_token = secrets['TRIGGER_TOKEN']
        self.project_id = int(secrets['PROJECT_ID'])

    def assign_secrets(self):
        filepath = os.path.expanduser('~/.gitlab-cli') + '/secrets.txt'
        if not os.path.exists(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write("SERVER=server_name\nTOKEN=token\nTRIGGER_TOKEN=trigger_token\nPROJECT_ID=1\n")
        with open(filepath, "r") as f:
            secrets = f.read().splitlines()
            secrets = self.convert_secrets_to_dict(secrets)
            self.assign_secrets_to_class(secrets)

    @staticmethod
    def format_output(runners, project_name):
        headers = [
            'NAME',
            'TAGS',
            'PROJECT',
            'ACTIVE JOBS',
            'STATUS',
        ]
        runners = sorted(runners, key=lambda i: i['description'])
        table = [[runner['description'],
                  ', '.join(runner['tag_list']) if len(runner['tag_list']) < 5 else ', '.join(
                      runner['tag_list'][:4]) + ' ...',
                  project_name, runner['active_jobs'], runner['status']] for runner in
                 runners]
        return tabulate(table, headers)

    def run_pipeline(self):
        return self.api.run_pipeline(self.branch, self.project_id, self.variables)

    def filter_runners(self, current_runners, filter_name, filter_values):
        if filter_name == Filtering.NAMES:
            return self.api.filter_by_names_dict(current_runners, filter_values)
        elif filter_name == Filtering.TAGS:
            return self.api.get_projects_filtered_runners_by_tags(current_runners, filter_values)

    def relative_complement_of_runners(self, runners, runners_to_ignore):
        new_runners = []
        for runner in runners:
            if runner not in runners_to_ignore:
                new_runners.append(runner)
        return new_runners

    def ignore_runners(self, runners):
        if self.ignore[0].lower() == 'tag':
            tags = self.ignore[1:]
            runners_to_ignore = self.filter_runners(runners, Filtering.TAGS, tags)
        elif self.ignore[0].lower() == 'name':
            names = self.ignore[1:]
            runners_to_ignore = self.filter_runners(runners, Filtering.NAMES, names)
        return self.relative_complement_of_runners(runners, runners_to_ignore)

    def get_filtered_runners(self):
        runners = self.api.get_projects_runners(self.project_id)
        runners = self.api.assign_tags_to_runners_asyncio(runners)
        if self.names:
            runners = self.filter_runners(runners, Filtering.NAMES, self.names)
        elif self.tags:
            runners = self.filter_runners(runners, Filtering.TAGS, self.tags)
        if self.ignore:
            runners = self.ignore_runners(runners)
        return runners

    def make_action_on_runners(self, runners):
        if self.action[0] == Actions.PAUSE.value:
            runners = self.api.change_runners_dict_status(runners, False)
        elif self.action[0] == Actions.RESUME.value:
            runners = self.api.change_runners_dict_status(runners, True)
        elif self.action[0] == Actions.RETAG.value:
            runners = self.retag_runners(runners)
        runners = self.api.assign_active_jobs_to_runners(runners, self.project_id)
        project_name = self.api.get_project(self.project_id).name
        return self.format_output(runners, project_name)

    def get_filtered_data(self):
        # todo check command line arguments
        if self.property_name == PropertyName.RUNNERS.value:
            runners = self.get_filtered_runners()
            return self.make_action_on_runners(runners)
        elif self.property_name == PropertyName.PIPELINE.value:
            return self.api.run_pipeline(self.branch, self.project_id, self.variables)

    def valid_retag_params(self) -> bool:
        """
        Checking if users put correct retag params
        EXAMPLE:
        runners retag old1:new1,old2:new2
        :return: BOOL
        """
        if not (self.action[0] == Actions.RETAG.value):
            return False
        pairs = self.action[1].split(',')
        for pair in pairs:
            if not self.correct_retag_pair(pair):
                return False
        return True

    @staticmethod
    def correct_retag_pair(pair):
        return len(pair.split(':')) == 2

    def get_tags_to_change(self):
        tags_to_change = self.action[1].split(',')
        return [pair.split(':') for pair in tags_to_change]

    def retag_runners(self, runners):
        if not self.valid_retag_params():
            raise RuntimeError("Wrong retag arguments. HINT: runners retag old1:new1,old2:new2 ...")
        tags_to_change = self.get_tags_to_change()
        runners_after_changes = []
        for runner in runners:
            changed, new_runner = self.retag_algorithm(runner, tags_to_change)
            runners_after_changes.append((changed, runner, new_runner))
        self.inform_user_about_changes(runners_after_changes)
        if self.ask_for_change():
            self.commit_changes_to_runners([new_runner for changed, runner, new_runner in runners_after_changes if changed])
        return [new_runner for changed, runner, new_runner in runners_after_changes]


    @staticmethod
    def inform_user_about_changes(runners_after_changes):
        for changed, runner, new_runner in runners_after_changes:
            if changed:
                print(runner['description'], 'changes: ', runner['tag_list'], ' -> ',
                      new_runner['tag_list'])
            else:
                print(runner['description'], "can't change")

    def ask_for_change(self):
        user_input = input("Do you want to change tags in runners? [Y/N]: ")
        if user_input.lower() in ['y', 'ye', 'yes']:
            return True
        print("Changes canceled.")
        return False

    def commit_changes_to_runners(self, runners_after_changes):
        print("Changing runners...")
        self.api.change_runners_dict_tags(runners_after_changes)
        return runners_after_changes

    @staticmethod
    def retag_algorithm(runner, tags_to_change):
        runner_after_changes = copy.deepcopy(runner)
        for old_tag, new_tag in tags_to_change:
            index_to_rename = runner_after_changes['tag_list'].index(old_tag)
            if index_to_rename < 0:
                print(f"{old_tag} not found in {runner_after_changes['tag_list']}")
                return False, runner
            runner_after_changes['tag_list'][index_to_rename] = new_tag
        return True, runner_after_changes

    @staticmethod
    def no_duplicates(tags):
        return len(tags) == len(set(tags))


class GitlabAPI:

    def __init__(self, server, token, trigger_token):
        self.server = server
        self.token = token
        self.gl = Gitlab(self.server, self.token)
        self.headers = {'PRIVATE-TOKEN': self.token}
        self.trigger_token = trigger_token

    @staticmethod
    def format_variables(variables: List[str]) -> Dict[str, str]:
        formatted_variables = {}
        for variable in variables:
            variable = variable.split('=')
            formatted_variables[variable[0]] = variable[1]
        return formatted_variables

    def run_pipeline(self, branch: str, project_id: int, variables: List[str]) -> Union[str, Exception]:
        """
        This function triggers pipeline with variables
        :param branch: name of branch
        :param project_id: id of project
        :param variables: variables for pipeline (optional)
        :return: url of pipeline
        """
        variables = variables or {}
        if variables:
            variables = self.format_variables(variables)
        project = self.get_project(project_id)
        try:
            pipeline = project.trigger_pipeline(branch, self.trigger_token, variables=variables)
            print(f'Pipeline for branch {branch} has been triggered')
            return pipeline.web_url
        except Exception as e:
            return e

    def assign_tags_to_runners_asyncio(self, runners: List[ProjectRunner]) -> List[dict]:
        runner_list = []
        runners_tags = asyncio.run(self.assign_tags_to_runners(runners))
        for runner, runner_tags in zip(runners, runners_tags):
            runner_obj = runner._attrs
            runner_obj['tag_list'] = runner_tags
            runner_list.append(runner_obj)
        return runner_list

    async def assign_tags_to_runners(self, runners: List[ProjectRunner]) -> List[List]:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for runner in runners:
                task = self.get_runners_tag_list(runner, session)
                tasks.append(task)
            runners_tags = await asyncio.gather(*tasks, return_exceptions=True)
            return runners_tags

    async def get_runners_tag_list(self, runner: ProjectRunner, session: ClientSession) -> List:
        runner_id = runner._attrs['id']
        url = f"{self.server}/api/v4/runners/{runner_id}"
        async with session.get(url, headers=self.headers) as response:
            runner_tag_list = await response.json()
            return runner_tag_list['tag_list']

    @staticmethod
    def filter_by_names(runners: List[ProjectRunner], names: List[str]) -> List[int]:
        if not isinstance(names, list):
            raise RuntimeError(f'"names" must be a list, {type(names)} was passed!')
        filtered_runners = []
        for runner in runners:
            for name in names:
                if name.lower() in runner.description.lower():
                    filtered_runners.append(runner)
        return list(set([runner.id for runner in filtered_runners]))

    @staticmethod
    def filter_by_names_dict(runners: List[dict], names: List[str]) -> List[dict]:
        if not isinstance(names, list):
            raise RuntimeError(f'"names" must be a list, {type(names)} was passed!')
        filtered_runners = []
        for runner in runners:
            for name in names:
                if name.lower() in runner['description'].lower():
                    filtered_runners.append(runner)
                    break
        return filtered_runners

    def get_projects_filtered_runners_by_name(self, project_id, names):
        projects_runners = self.get_projects_runners(project_id)
        all_filtered_runners = self.filter_by_names(projects_runners, names)
        return [runner for runner in projects_runners if runner.id in all_filtered_runners]

    def get_projects_filtered_runners_by_tags(self, runners: List[dict], tags: List[str]) -> List[dict]:
        if not isinstance(tags, list):
            raise RuntimeError(f'"tags" must be a list, {type(tags)} was passed!')
        filtered_runners = []
        for runner in runners:
            for tag in tags:
                if self.check_if_tag_in_list(tag, runner['tag_list']):
                    filtered_runners.append(runner)
                    # break to not to duplicate runners
                    break
        return filtered_runners

    def check_if_tag_in_list(self, tag, list_of_runner_tags):
        new_list_of_tags = [runner_tag.lower() for runner_tag in list_of_runner_tags]
        # check if tag.lower is a part of any tag from tag_list
        for runner_tag in new_list_of_tags:
            if tag.lower() in runner_tag.lower():
                return True
        return False

    def get_projects_runners(self, project_id):
        return self.get_project(project_id).runners.list(all=True)

    def get_runners_by_tags(self, tags, project_id):
        """
        Function merges requests from gitlabapi and return runners with OR statement between tags.
        Function looks for EXACT names of tags.
        :param project_id
        :param tags:
        :return: list of tags
        """

        runners = []
        if tags:
            for tag in tags:
                url = f'{self.server}/api/v4/projects/{project_id}/runners/all?tag_list={tag}&per_page=100'
                runners += self.handle_pagination(url)
        else:
            url = f'{self.server}/api/v4/runners/all?per_page=100'
            runners = self.handle_pagination(url)
        return runners

    @staticmethod
    def format_tag_list(tags: List) -> str:
        if not tags:
            return ''
        return ','.join(tags)

    def handle_pagination(self, url):
        response = requests.get(url, headers=self.headers)
        data = response.json()
        link, state = [x.split(';') for x in response.headers['Link'].split(',')][0]
        link = link.strip()
        while 'next' in state:
            response = requests.get(link[1:-1], headers=self.headers)
            data += response.json()
            link, state = [x.split(';') for x in response.headers['Link'].split(',')][1]
            link = link.strip()
        return data

    def get_project(self, id):
        return self.gl.projects.get(id)

    def list_all_projects(self):
        return self.gl.projects.list(all=True)

    def list_all_runners(self):
        return self.gl.runners.list(all=True)

    def assign_active_jobs_to_runners(self, runners, project_id):
        jobs = self.get_running_jobs_from_project(project_id)
        counted_jobs_for_runners = self.count_jobs_for_runners(jobs)
        for runner in runners:
            if runner['id'] in counted_jobs_for_runners:
                runner['active_jobs'] = counted_jobs_for_runners[runner['id']]
            else:
                runner['active_jobs'] = 0
        return runners

    def get_running_jobs_from_project(self, project_id):
        url = f'{self.server}/api/v4/projects/{project_id}/jobs?scope[]=running&per_page=100'
        return self.handle_pagination(url)

    @staticmethod
    def count_jobs_for_runners(jobs):
        counted_jobs = {}  # number in dict is equal to runner id
        for job in jobs:
            if job['runner']['id'] in counted_jobs:
                counted_jobs[job['runner']['id']] += 1
            else:
                counted_jobs[job['runner']['id']] = 1
        return counted_jobs

    def change_runners_dict_status(self, runners: List[dict], status: bool) -> List[dict]:
        """
        Function which pauses or resumes all selected runners
        :param runners: List of runners [dict]
        :param status: True (Resume) / False (Pause)
        :return: List of runners [dict]
        """
        payload = {'active': status}
        for runner in runners:
            try:
                url = f'{self.server}/api/v4/runners/{runner["id"]}'
                response = requests.put(url, headers=self.headers, data=payload)
                response.raise_for_status()
                if status:
                    runner['status'] = 'online'
                    print(f'Runner id: {runner["id"]} is resumed')
                else:
                    runner['status'] = 'paused'
                    print(f'Runner id: {runner["id"]} is paused')
            except Exception as err:
                if status:
                    print(f'Runner {runner["id"]} cannot be resumed because of {err}')
                else:
                    print(f'Runner {runner["id"]} cannot be paused because of {err}')

        return runners

    def change_runners_dict_tags(self, runners_after_changes: List[dict]) -> List[dict]:
        """
        Function which commits changes to runners tags
        :param runners_after_changes: List of runners [dict]
        :return: List of runners [dict]
        """
        for runner in runners_after_changes:
            try:
                url = f'{self.server}/api/v4/runners/{runner["id"]}'
                payload = {'tag_list': ','.join(runner['tag_list'])}
                response = requests.put(url, headers=self.headers, data=payload)
                response.raise_for_status()
                print(f'Runner id: {runner["id"]} tags changed.')
            except Exception as err:
                print(f'Runner {runner["id"]} cannot be changed because of {err}')
        return runners_after_changes
