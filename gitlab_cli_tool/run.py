import shlex

from fuzzyfinder.main import fuzzyfinder
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory

from gitlab_cli import GitLabCLI
from gitlab_cli_tool.cli_api import PropertyName, Actions

GitlabCLIKeywords = [property_name.value for property_name in PropertyName] + [action.value for action in Actions] + [
    '--branch', '--tag', '--name', '--variables']


class GitlabCLICompleter(Completer):
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        matches = fuzzyfinder(word_before_cursor, GitlabCLIKeywords)

        for m in matches:
            yield Completion(m, start_position=-len(word_before_cursor))


def main():
    while 1:
        try:
            user_input = prompt(u'Gitlabcli > ',
                                history=FileHistory('history.txt'),
                                auto_suggest=AutoSuggestFromHistory(),
                                completer=GitlabCLICompleter(),
                                )
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            try:
                input = shlex.split(user_input)
                print(GitLabCLI().get_result(input))
            except SystemExit:
                pass
    print('Exited.')


if __name__ == '__main__':
    main()
