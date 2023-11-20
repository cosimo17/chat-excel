from src.interpreter import PythonInterpreter, wrap_in_try_except
from src.utis import decodestdoutput
import pandas as pd


def test_interpreter():
    python_interp = PythonInterpreter()
    code = "import pandas as pd\n" \
           "import pickle\n\n" \
           "df = pd.DataFrame({'A': list(range(2)), 'B': list(range(2))})\n" \
           "print(pickle.dumps(df))"
    code = wrap_in_try_except(code)
    for i in range(2):
        stdout, stderr = python_interp.execute(code)
        data = decodestdoutput(stdout)
        assert isinstance(data, pd.DataFrame)
        assert data.shape == (2, 2)
