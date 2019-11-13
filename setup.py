import os

from setuptools import find_packages
from setuptools import setup


def create_credentials_folder():
    filepath = os.path.expanduser('~/.gitlab-cli') + '/secrets.txt'
    if not os.path.exists(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write("SERVER=server_name\nTOKEN=token\nTRIGGER_TOKEN=trigger_token\nPROJECT_ID=1\n")


create_credentials_folder()

with open('requirements.txt') as f:
    required = f.read().splitlines()

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name='gitlab_cli_tool',
    version='1.0',
    description='CLI for Gitlab',
    long_description=readme,
    author='Jakob Wolitzki',
    author_email='j.wolitzki@gastrofix.com',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['gitlabcli=gitlab_cli_tool.gitlab_cli:main'],
    },
    install_requires=required
)
