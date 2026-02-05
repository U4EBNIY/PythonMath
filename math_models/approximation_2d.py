import numpy as np
from scipy.interpolate import griddata
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


class Approximation2D:
    description = 'Аппроксимация 2D: Z = f(X, Y)'
    input_name = 'X1,X2'
    output_name = 'Y'
    io_desc = 'Входные/выходные переменные'
    io_unit = 'ед.'

    def __init__(self, coefs=None):
        if coefs is None:
            coefs = self._get_default_coefs()
        self.coefs = coefs
        self.data_x1 = None
        self.data_x2 = None
        self.data_y = None
        self.model = None
        self.mode = coefs.get('approximation_mode', '0')
        self.file_path = coefs.get('excel_file_path', '')
        self.is_initialized = False

    def _get_default_coefs(self):
        return {
            'excel_file_path': 'test_data/test_2d.xlsx',
            'approximation_mode': '0'
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

    @property
    def input_names(self):
        return ['X1', 'X2']

    def calculate_batch(self, x1_inputs, x2_inputs):
        results = []
        for x1, x2 in zip(x1_inputs, x2_inputs):
            results.append(self.calculate(x1, x2))
        return results

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
        self.data_x1, self.data_x2, self.data_y = ExcelReader.read_2d_data(actual_path)

        if self.mode == '0':
            print(f"Построение полинома 2D...")
            X = np.column_stack([
                self.data_x1 ** 2,
                self.data_x2 ** 2,
                self.data_x1 * self.data_x2,
                self.data_x1,
                self.data_x2,
                np.ones_like(self.data_x1)
            ])
            self.model = np.linalg.lstsq(X, self.data_y, rcond=None)[0]
            print(f"Коэффициенты полинома: {self.model}")

        self.is_initialized = True
        print(f"Модель построена, точек: {len(self.data_x1)}")

    def calculate(self, x1_input, x2_input):
        if not self.is_initialized:
            raise RuntimeError("Модель не инициализирована")

        if self.mode == '0':
            a, b, c, d, e, f = self.model
            result = (a * x1_input ** 2 + b * x2_input ** 2 +
                      c * x1_input * x2_input +
                      d * x1_input + e * x2_input + f)
            print(f"Вычисление: X1={x1_input}, X2={x2_input} -> Y={result}")
            return result
        else:
            points = np.column_stack((self.data_x1, self.data_x2))
            value = griddata(points, self.data_y, [(x1_input, x2_input)], method='linear')[0]
            result = float(value) if not np.isnan(value) else 0.0
            print(f"Вычисление: X1={x1_input}, X2={x2_input} -> Y={result}")
            return result