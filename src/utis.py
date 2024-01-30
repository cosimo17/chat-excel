from functools import wraps
import pickle
import ast
import re
import sys
import os


def withoutconnect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        win = args[0]
        win.itemChanged.disconnect()
        r = func(win, **kwargs)
        win.itemChanged.connect(win.handle_item_changed)
        return r

    return wrapper


def wrap_code(code, df):
    pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
    match = re.search(pattern, code)
    function_name = match.group(1)

    import_line = 'import pandas as pd\n' \
                  'import numpy as np\n' \
                  'import ast\n' \
                  'import sys\n' \
                  'import pickle\n\n'
    code = import_line + code
    data_line = 'df = {}\n' \
                'df = pickle.loads(df)\n'.format(pickle.dumps(df))
    code = code + data_line
    call_line = 'result = {}(df)\nprint(pickle.dumps(result))\n'.format(function_name)
    code = code + call_line
    return code


def extract_func_info(code, df):
    lines = code.split("\n")
    for line in lines:
        if is_assignment_statement(line):
            exec(line)

    pattern = re.compile(r'(\w+)\((.*?)\)')
    matches = pattern.findall(code)

    func_names = []
    func_args = []
    func_kwargs = []
    for match in matches:
        function_name = match[0]
        func_names.append(function_name)
        arguments = match[1]
        current_func_args = []
        current_func_kwargs = {}
        if len(arguments):
            arguments = arguments.split(',')
            arguments = [v.replace(' ', '') for v in arguments]
            for arg in arguments:
                # keyword arg
                if '=' in arg:
                    k, v = arg.split('=')
                    if is_subscript_and_index(v) or is_constant(v):
                        v = eval(v)
                    else:
                        v = v.replace("\'", '')
                    current_func_kwargs[k] = v
                else:
                    current_func_args.append(eval(arg))
        func_args.append(current_func_args)
        func_kwargs.append(current_func_kwargs)
    return func_names, func_args, func_kwargs


def decodestdoutput(output_from_std):
    output = ast.literal_eval(output_from_std)
    data = pickle.loads(output)
    return data


def is_assignment_statement(line):
    try:
        tree = ast.parse(line)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                return True
    except SyntaxError:
        return False

    return False


def is_subscript_and_index(line):
    try:
        tree = ast.parse(line)
        subscript, index = False, False
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                subscript = True
            elif isinstance(node, ast.Index):
                index = True
        return subscript and index
    except SyntaxError:
        return False


def is_constant(line):
    try:
        tree = ast.parse(line)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                return True
    except SyntaxError:
        return False

    return False


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
