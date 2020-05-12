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


def test_filtering_cases():
    pass