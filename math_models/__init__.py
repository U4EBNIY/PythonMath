from .approximation_1d import Approximation1D
from .approximation_2d import Approximation2D
from .interpolation_1d import Interpolation1D
from .interpolation_2d import Interpolation2D

# Словарь доступных моделей
Models = {
    'Аппроксимация 1D': Approximation1D,
    'Аппроксимация 2D': Approximation2D,
    'Интерполяция 1D': Interpolation1D,
    'Интерполяция 2D': Interpolation2D,
}