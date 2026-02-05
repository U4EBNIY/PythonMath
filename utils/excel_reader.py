import pandas as pd
import numpy as np


class ExcelReader:

    @staticmethod
    def read_1d_data(file_path: str):
        # Читает данные для 1D моделей, колонки X и Y
        df = pd.read_excel(file_path, engine='openpyxl')

        # Проверяем нужные колонки
        if 'X' not in df.columns or 'Y' not in df.columns:
            raise ValueError(f"В файле {file_path} должны быть колонки 'X' и 'Y'")

        # Берем данные
        x = df['X'].values.astype(float)
        y = df['Y'].values.astype(float)

        # Убираем строки где есть NaN
        valid = ~(np.isnan(x) | np.isnan(y))
        x, y = x[valid], y[valid]

        # Сортируем по X
        order = np.argsort(x)
        return x[order], y[order]

    @staticmethod
    def read_2d_data(file_path: str):
        # Читает данные для 2D моделей: колонки X1, X2 и Y
        df = pd.read_excel(file_path, engine='openpyxl')

        # Проверяем нужные колонки
        needed = ['X1', 'X2', 'Y']
        for col in needed:
            if col not in df.columns:
                raise ValueError(f"В файле {file_path} должна быть колонка '{col}'")

        # Берем данные
        x1 = df['X1'].values.astype(float)
        x2 = df['X2'].values.astype(float)
        y = df['Y'].values.astype(float)

        # Убираем строки где есть NaN
        valid = ~(np.isnan(x1) | np.isnan(x2) | np.isnan(y))
        return x1[valid], x2[valid], y[valid]