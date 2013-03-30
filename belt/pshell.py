import os
import sys
import importlib
from pyramid.scripts import pshell


class Shell(pshell.PShellCommand):

    def make_shell(self):
        try:
            start = os.environ['PYTHONSTARTUP']
        except KeyError:
            return super(Shell, self).make_shell()

        dirname = os.path.dirname(start)
        module = os.path.basename(start)
        module, _ = os.path.splitext(module)
        sys.path.insert(0, dirname)
        mod = importlib.import_module(module, os.path.basename(dirname))
        sys.path.pop(0)

        def shell(env, help):
            code = mod.EditableBufferInteractiveConsole(locals=env)
            code.interact(help + "\n\n")
        return shell


def pshell():
    pass


if __name__ == "__main__":
    command = Shell(sys.argv)
    command.run()
