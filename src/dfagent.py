from src.memo import TableMemo, Modification, TableSnapShot, ModificationType, build_item_info
from src.observer import Observer
import pandas as pd


class DataFrameAgent(Observer):
    def __init__(self):
        self.df = None

    def load(self, excel_file):
        self.df = pd.read_excel(excel_file)

    def _update(self, subject):
        modifications = subject.modification
        mtype = modifications.mtype
        if mtype != ModificationType.RESET:
            return
        # TODO 将答案作为新的工作表

    def insert_row(self, item_infos):
        if len(item_infos) == 0:
            return
        new_row_data = {}
        for col_name, item_info in zip(self.df.columns, item_infos):
            new_row_data[col_name] = item_info.dtype(item_info.text)

        row_index = item_infos[0].index[0]
        if row_index == len(self.df):
            self.df.loc[len(self.df)] = new_row_data
        else:
            pd.concat([self.df.iloc[:row_index], pd.DataFrame([new_row_data]), self.df.iloc[row_index:]]).reset_index(
                drop=True)

    def insert_column(self, item_infos):
        new_column_data = []
        for item_info in item_infos:
            new_column_data.append(item_info.dtype(item_info.text))
        new_column_name = item_infos[0].column_name
        insert_position = item_infos[0].index[1]
        self.df.insert(insert_position, new_column_name, new_column_data)

    def delete_row(self, item_infos):
        if len(item_infos):
            item_info = item_infos[0]
            index = item_info.index
            row, column = index
            self.df = self.df.drop(row)

    def delete_column(self, item_infos):
        if len(item_infos) == 0:
            return
        item_info = item_infos[0]
        column_name_to_delete = item_info.column_name
        del self.df[column_name_to_delete]

    def update_inplace(self, item_infos):
        for item_info in item_infos:
            row, column = item_info.index
            value = item_info.text
            dtype = item_info.dtype
            self.df.iloc[row, column] = dtype(value)

    @property
    def shape(self):
        if self.df is not None:
            return self.df.shape

    @property
    def dtypes(self):
        if self.df is not None:
            return self.df.dtypes

    def head(self, n=3):
        if self.df is not None:
            return self.df.head(n)
