"""Registry for CLI commands; jobs register with @command."""

COMMANDS = {}


def command(name):
    def register(func):
        COMMANDS[name] = func
        return func

    return register
