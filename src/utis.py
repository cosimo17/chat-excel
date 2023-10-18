from functools import wraps
import pickle


def withoutconnect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        self.table_widget.itemChanged.disconnect()
        r = func(self)
        self.table_widget.itemChanged.connect(self.handle_item_changed)

    return wrapper


def wrap_code(code, df):
    import_line = 'import pandas as pd\n' \
                  'import numpy as np\n' \
                  'import ast\n' \
                  'import sys\n' \
                  'import pickle\n\n'
    code = import_line + code
    data_line = 'df = {}\n' \
                'df = pickle.loads(df)\n'.format(pickle.dumps(df))
    code = code + data_line
    call_line = 'result = function(df)\nprint(pickle.dumps(result))\n'
    code = code + call_line
    return code
