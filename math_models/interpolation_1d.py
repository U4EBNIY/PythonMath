import numpy as np
import bisect
import sys
import os


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.excel_reader import ExcelReader


class Interpolation1D:
    description = ('Интерполяция 1D: Y = f(X) - вычисление промежуточных значений между известными точками.'
                   ' Формат Excel: столбцы X и Y. Режимы: 0 - Кусочно-линейная, 1 - Ступенчатая')
    input_name = 'X'
    output_name = 'Y'
    io_desc = 'Входная/выходная переменная'
    io_unit = 'ед.'

    def __init__(self, coefs=None):
        if coefs is None:
            coefs = self._get_default_coefs()
        self.coefs = coefs
        self.data_x = None
        self.data_y = None
        self.mode = coefs.get('interpolation_mode', '0')
        self.file_path = coefs.get('excel_file_path', '')
        self.is_initialized = False

    def _get_default_coefs(self):
        return {
            'excel_file_path': 'test_data/test_1d.xlsx',
            'interpolation_mode': '0'
        }

    @property
    def model_desc(self):
        return self.description

    @property
    def io_descr(self):
        return self.io_desc

    @property
    def io_units(self):
        return self.io_unit

    @property
    def output(self):
        return self.output_name

    @property
    def input(self):
        return self.input_name

    def load_data(self):
        actual_path = get_resource_path(self.file_path)
        print(f"Загрузка данных из: {actual_path}")

        if not os.path.exists(actual_path):
            if os.path.exists(self.file_path):
                actual_path = self.file_path
            else:
                possible_paths = [
                    self.file_path,
                    os.path.join('test_data', os.path.basename(self.file_path)),
                    os.path.join(os.getcwd(), self.file_path),
                    os.path.join(os.getcwd(), 'test_data', os.path.basename(self.file_path))
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        actual_path = path
                        break
                else:
                    raise FileNotFoundError(f"Excel файл не найден: {self.file_path}")

        print(f"Используем файл: {actual_path}")
        self.data_x, self.data_y = ExcelReader.read_1d_data(actual_path)

        if len(self.data_x) == 0:
            raise ValueError("Excel файл не содержит данных")

        self.is_initialized = True
        print(f"Загружено {len(self.data_x)} точек")
        print(f"Диапазон X: {self.data_x[0]:.2f} ... {self.data_x[-1]:.2f}")
        print(f"Режим: {'кусочно-линейная' if self.mode == '0' else 'ступенчатая'}")

    def calculate(self, x_input):
        if not self.is_initialized:
            raise RuntimeError("Модель не инициализирована")

        if x_input <= self.data_x[0]:
            return self.data_y[0]
        if x_input >= self.data_x[-1]:
            return self.data_y[-1]

        if self.mode == '0':
            return self._linear_interpolation(x_input)
        else:
            return self._step_interpolation(x_input)

    def _linear_interpolation(self, x):
        idx = bisect.bisect_right(self.data_x, x)

        x_left = self.data_x[idx - 1]
        x_right = self.data_x[idx]
        y_left = self.data_y[idx - 1]
        y_right = self.data_y[idx]

        return y_left + (y_right - y_left) * (x - x_left) / (x_right - x_left)

    def _step_interpolation(self, x):
        idx = bisect.bisect_right(self.data_x, x) - 1
        return self.data_y[idx]