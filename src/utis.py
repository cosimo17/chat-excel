from functools import wraps
import pickle
import ast
import re


def withoutconnect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        self.table_widget.itemChanged.disconnect()
        r = func(self)
        self.table_widget.itemChanged.connect(self.handle_item_changed)

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


def extract_func_info(code):
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
                if '=' in arg:
                    k, v = arg.split('=')
                    v = v.replace("\'", '')
                    current_func_kwargs[k] = v
                else:
                    current_func_args.append(arg)
        func_args.append(current_func_args)
        func_kwargs.append(current_func_kwargs)
    return func_names, func_args, func_kwargs


def decodestdoutput(output_from_std):
    output = ast.literal_eval(output_from_std)
    data = pickle.loads(output)
    return data
