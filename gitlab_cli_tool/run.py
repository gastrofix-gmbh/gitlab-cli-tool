import shlex

from fuzzyfinder.main import fuzzyfinder
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory

from cli_api import PropertyName, Actions
from gitlab_cli import GitLabCLI

GitlabCLIKeywords = [property_name.value for property_name in PropertyName] + [action.value for action in Actions] + [
    '--branch', '--tag', '--name', '--variables']


class GitlabCLICompleter(Completer):
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        matches = fuzzyfinder(word_before_cursor, GitlabCLIKeywords)

        for m in matches:
            yield Completion(m, start_position=-len(word_before_cursor))


def main():
    keyboard_interrupt = 0
    while 1:
        try:
            user_input = prompt(u'Gitlabcli > ',
                                history=FileHistory('history.txt'),
                                auto_suggest=AutoSuggestFromHistory(),
                                completer=GitlabCLICompleter(),
                                )
            keyboard_interrupt = 0
            if user_input.lower() == 'exit' or user_input.lower() == 'quit':
                break
        except KeyboardInterrupt:
            keyboard_interrupt += 1
            if keyboard_interrupt == 2:
                break
            print("Are you sure you want to exit? Ctrl + C to exit")
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
