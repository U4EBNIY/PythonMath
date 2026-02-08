import numpy as np
from scipy.interpolate import splrep, splev
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


class Approximation1D:
    description = ('Аппроксимация 1D: Y = f(X) - построение приближающей функции по экспериментальным точкам. '
                   'Формат Excel: столбцы X и Y. Режимы: 0 - Полином 2-й степени,'
                   ' 1 - Cплайн')
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
        self.model = None
        self.mode = coefs.get('approximation_mode', '0')
        self.file_path = coefs.get('excel_file_path', '')
        self.is_initialized = False

    def _get_default_coefs(self):
        return {
            'excel_file_path': 'test_data/test_1d.xlsx',
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

        if self.mode == '0':
            print(f"Построение полинома 2-й степени...")
            self.model = np.polyfit(self.data_x, self.data_y, 2)
            print(f"Коэффициенты полинома: {self.model}")
        else:
            print(f"Построение сплайна...")
            self.model = splrep(self.data_x, self.data_y, s=0)

        self.is_initialized = True
        print(f"Модель построена, точек: {len(self.data_x)}")

    def calculate(self, x_input):
        if not self.is_initialized:
            raise RuntimeError("Модель не инициализирована")

        if self.mode == '0':
            result = np.polyval(self.model, x_input)
            print(f"Вычисление: X={x_input} -> Y={result}")
            return result
        else:
            result = splev(x_input, self.model)
            print(f"Вычисление: X={x_input} -> Y={result}")
            return result