from src.utis import *

def test_decode():
    data = b'\x80\x04K{.'
    res = decodestdoutput(str(data))
    assert res == 123

    data = b'\x80\x04\x88.'
    res = decodestdoutput(str(data))
    assert res == True


def test_is_assignment_statement():
    code = "a = 123"
    assert is_assignment_statement(code)
    code = "print(123)"
    assert not is_assignment_statement(code)


def test_is_subscript_and_index():
    code = "data['123']"
    assert is_subscript_and_index(code)
    code = "a = data.name"
    assert not is_subscript_and_index(code)


def test_extract_func_info():
    import pandas as pd
    df = pd.read_excel("../温度.xlsx")
    code = "month = df['month']\n" \
           "temp = df['temperature']\n" \
           "ax.plot(month, temp, color='r')"
    func_names, func_args, func_kwargs = extract_func_info(code, df)
    assert (func_args[0][0] == df['month']).all()
    assert (func_args[0][1] == df['temperature']).all()
    assert func_names[0] == 'plot'
    assert 'color' in list(func_kwargs[0].keys())
    assert func_kwargs[0].get('color') == 'r'