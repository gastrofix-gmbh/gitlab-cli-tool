#!/usr/bin/env python3
import argparse
import sys

from gitlab_cli_tool.cli_api import GitLabDataFilter, PropertyName, Actions


class GitLabCLI:
    def __init__(self):
        self.property_name = ''
        self.action = ''
        self.tags = []
        self.names = []
        self.branch = ''
        self.variables = []
        self.ignore = []

    @staticmethod
    def parse_args(args):
        parser = argparse.ArgumentParser(
            description='CLI for GitLab, to exit CTRL + D'
        )

        parser.add_argument('property_name', help='Projects, Runners, etc',
                            choices=[property_name.value for property_name in PropertyName],
                            default='runners')

        parser.add_argument('action', help='What to do with property, list, pause, resume',
                            default='list',
                            nargs='*',
                            )
        parser.add_argument('-b', '--branch', help='Triggering by branch name', nargs=1)
        parser.add_argument('-t', '--tag', help='Filtering by tags', nargs='+')
        parser.add_argument('-n', '--name', help='Filtering by name', nargs='+')
        parser.add_argument('-v', '--variables', help='Triggering branch with variables, format key=value', nargs='+')
        parser.add_argument('-i', '--ignore',
                            help="Ignore runners, first specify if ignore by 'name' or 'tag', example 'runners list --name qa01 --ignore tag qa01-1'",
                            nargs='+')
        return parser.parse_args(args)

    def check_variables(self):
        for variable in self.variables:
            if not len(variable.split('=')) == 2:
                return False
        return True

    def check_filters(self):
        # TODO check all combination, write function for checking that. Maybe group arguments together
        if self.tags and self.names:
            print('Tag and names cannot be filtered together')
            return False
        if self.tags and self.branch:
            print('Tag and branch cannot be filtered together')
            return False
        if self.branch and self.names:
            print('Names and branch cannot be filtered together')
            return False
        # TODO variables need to be associated with pipeline
        if self.variables:
            if not self.check_variables():
                raise RuntimeError(
                    f'Variables passed have wrong format. Expected format: key=value Actual: {self.variables}')
        if len(self.action) > 1:
            if self.action[0] != Actions.RETAG.value:
                print(f"{self.action[0]} can't have more arguments")
                return False
        if len(self.action) > 2:
            print("Wrong arguments")
            return False
        return True

    def assign_args_to_cli(self, args):
        """
        Assigning arguments from parser to class
        User may pass more than one tag or name
        there is logical OR between names or between tags
        :param args: list of arguments
        :return: None
        """
        parsed_args = self.parse_args(args)
        self.property_name = parsed_args.property_name
        self.action = parsed_args.action
        self.tags = parsed_args.tag
        self.names = parsed_args.name
        self.branch = parsed_args.branch[0] if parsed_args.branch else parsed_args.branch
        self.variables = parsed_args.variables
        self.ignore = parsed_args.ignore

    def get_result(self, args):
        self.assign_args_to_cli(args)
        if not self.check_filters():
            return 'No data'
        data_filter = GitLabDataFilter(property_name=self.property_name, action=self.action, tags=self.tags,
                                       names=self.names, branch=self.branch, variables=self.variables,
                                       ignore=self.ignore)
        message = data_filter.get_filtered_data()
        return message


def main():
    print(GitLabCLI().get_result(sys.argv[1:]))


if __name__ == '__main__':
    main()
