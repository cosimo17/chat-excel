import subprocess
import sys
import ast
import astunparse
import pandas as pd
import pickle


def wrap_in_try_except(code):
    # Add import traceback
    code = "import traceback\n" + code

    # Parse the input code into an AST
    parsed_code = ast.parse(code)

    # Wrap the entire code's AST in a single try-except block
    try_except = ast.Try(
        body=parsed_code.body,
        handlers=[
            ast.ExceptHandler(
                type=ast.Name(id="Exception", ctx=ast.Load()),
                name=None,
                body=[
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(value=ast.Name(id="traceback", ctx=ast.Load()), attr="print_exc",
                                               ctx=ast.Load()),
                            args=[],
                            keywords=[]
                        )
                    ),
                ]
            )
        ],
        orelse=[],
        finalbody=[]
    )

    # Assign the try-except block as the new body
    parsed_code.body = [try_except]

    # Convert the modified AST back to source code

    return astunparse.unparse(parsed_code)


class PythonInterpreter(object):
    def __init__(self):
        self.start_cmd = [sys.executable, '-i', '-q', '-u']
        self.process = None

    def start_subprocess(self):
        # recreate new subprocess for each call
        if self.process is not None:
            self.process.kill()
        self.process = subprocess.Popen(self.start_cmd,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        bufsize=0,
                                        encoding='utf-8')

    def execute(self, code):
        self.start_subprocess()
        self.process.stdin.write(code)
        self.process.stdin.close()  # Important: close stdin to signal that no more input will be sent
        stdout, stderr = self.process.communicate()
        return stdout, stderr
