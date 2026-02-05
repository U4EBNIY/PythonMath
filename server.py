import grpc
from concurrent import futures
import traceback

# Импорт protobuf файлов
import MathApi_pb2
import MathApi_pb2_grpc

# Импорт моделей
from math_models import Models


class ModelManager:
    # Класс для управления моделями

    def __init__(self):
        # Словарь для хранения моделей
        self.models = {}

    def create_model(self, model_id, model_name, constants):
        # Создание новой модели.
        # Если модель с таким ID уже существует, nj удаляем
        if model_id in self.models:
            self.remove_model(model_id)

        # Проверяем, что модель доступна
        if model_name not in Models:
            return False

        try:
            # Экземпляр модели
            model = Models[model_name](constants)
            # Загружаем данные для модели
            model.load_data()

            # Сохраняем в словаре
            self.models[model_id] = {
                'instance': model,  # экземпляр модели
                'name': model_name,  # название модели
                'constants': constants  # константы модели
            }

            print(f"Создана модель: {model_name} (id: {model_id})")
            return True

        except Exception:
            # При ошибке
            traceback.print_exc()
            return False

    def get_model(self, model_id):
        # Получить модель по ID
        return self.models.get(model_id)

    def remove_model(self, model_id):
        # Удалить модель по ID
        if model_id in self.models:
            del self.models[model_id]
            print(f"Удалена модель: {model_id}")
            return True
        return False

    def calculate(self, model_id, inputs):
        # Вычислить результат с помощью модели.
        # Получаем данные модели
        model_data = self.get_model(model_id)
        if not model_data:
            return None

        model = model_data['instance']
        model_name = model_data['name']

        try:
            # Определяем тип модели и вызываем метод
            if '1D' in model_name:
                # Для 1D моделей берем последнее значение из массива
                if len(inputs) == 0:
                    return None
                last_value = inputs[-1]
                print(f"1D: X={last_value} (из {len(inputs)} значений)")
                return model.calculate(last_value)

            elif '2D' in model_name:
                # Для 2D моделей нужны два последних значения
                if len(inputs) < 2:
                    return None
                x1 = inputs[-2] if len(inputs) >= 2 else inputs[0]
                x2 = inputs[-1]
                print(f"2D: X1={x1}, X2={x2}")
                return model.calculate(x1, x2)

            else:
                return None

        except Exception:
            traceback.print_exc()
            return None


class MathApi(MathApi_pb2_grpc.MathApiServicer):
    #Основной класс gRPC

    def __init__(self):
        # Менеджер моделей
        self.model_manager = ModelManager()

    def GetModels(self, request, context):
        # Получить список доступных моделей
        try:
            items = []
            for name, model_class in Models.items():
                # Экземпляр для получения описания
                model = model_class()
                items.append(MathApi_pb2.ModelName(name=name, desc=model.model_desc))
            return MathApi_pb2.Models(modelNames=items)
        except Exception as e:
            return MathApi_pb2.Models(message=f"Err_{str(e)}")

    def GetConstants(self, request, context):
        # Получить константы для указанной модели
        try:
            model_name = request.modelName
            if model_name not in Models:
                return MathApi_pb2.Constants(message=f"Err_Модель '{model_name}' не найдена")

            # Создаем модель и получаем константы
            model = Models[model_name]()
            constants = []
            for name, value in model.coefs.items():
                constants.append(MathApi_pb2.Constant(name=name, value=str(value)))
            return MathApi_pb2.Constants(constantValues=constants)
        except Exception as e:
            return MathApi_pb2.Constants(message=f"Err_{str(e)}")

    def GetInputTags(self, request, context):
        # Получить описание входных тегов для модели
        try:
            model_name = request.modelName
            if model_name not in Models:
                return MathApi_pb2.Tags(message=f"Err_Модель '{model_name}' не найдена")

            model = Models[model_name]()
            tags = []

            # Входные теги от типа модели
            if '1D' in model_name:
                tags.append(MathApi_pb2.TagType(name="X", desc="Входная переменная", unit=model.io_units))
            elif '2D' in model_name:
                tags.append(MathApi_pb2.TagType(name="X1", desc="Первая входная переменная", unit=model.io_units))
                tags.append(MathApi_pb2.TagType(name="X2", desc="Вторая входная переменная", unit=model.io_units))

            return MathApi_pb2.Tags(tags=tags)
        except Exception as e:
            return MathApi_pb2.Tags(message=f"Err_{str(e)}")

    def GetOutputTags(self, request, context):
        # Описание выходных тегов для модели
        try:
            model_name = request.modelName
            if model_name not in Models:
                return MathApi_pb2.Tags(message=f"Err_Модель '{model_name}' не найдена")

            model = Models[model_name]()
            # Для всех моделей есть один выходной тег Y
            tags = [MathApi_pb2.TagType(
                name="Y",
                desc="Выходная переменная",
                unit=model.io_units
            )]
            return MathApi_pb2.Tags(tags=tags)
        except Exception as e:
            return MathApi_pb2.Tags(message=f"Err_{str(e)}")

    def Start(self, request, context):
        # Запуск модели
        try:
            model_id = request.modelId
            model_name = request.modelName
            # Константы  в словарь
            constants = {const.name: const.value for const in request.constants}

            print(f"Start: {model_name} (id: {model_id})")
            success = self.model_manager.create_model(model_id, model_name, constants)

            if success:
                return MathApi_pb2.RetReply(message="Start успешен")
            else:
                return MathApi_pb2.RetReply(message="Err_Не удалось создать модель")
        except Exception as e:
            return MathApi_pb2.RetReply(message=f"Err_{str(e)}")

    def Transform(self, request, context):
        try:
            model_id = request.modelId
            print(f"Transform для модели {model_id}")

            # Входные значения из тегов
            inputs = []
            for tag in request.tagsVal:
                inputs.append(tag.numericValue)

            print(f"Получено {len(inputs)} значений")

            # Вычисляем результат
            result = self.model_manager.calculate(model_id, inputs)

            if result is not None:
                # Временная метку последнего тега
                timestamp = request.tagsVal[-1].timeStamp if request.tagsVal else 0

                # Ответ
                response = MathApi_pb2.TagsDataArray()
                response.tagsVal.append(MathApi_pb2.TagVal(
                    tagName="Y",
                    timeStamp=timestamp,
                    numericValue=float(result),
                    isGood=True
                ))
                print(f"Результат: Y={result}")
                return response
            else:
                return MathApi_pb2.TagsDataArray(message="Err_Ошибка вычисления")
        except Exception as e:
            print(f"Ошибка Transform: {e}")
            traceback.print_exc()
            return MathApi_pb2.TagsDataArray(message=f"Err_{str(e)}")

    def Stop(self, request, context):
        # Остановка модели
        try:
            model_id = request.modelId
            print(f"Stop: {model_id}")
            success = self.model_manager.remove_model(model_id)

            if success:
                return MathApi_pb2.RetReply(message="Stop успешен")
            else:
                return MathApi_pb2.RetReply(message="Err_Модель не найдена")
        except Exception as e:
            return MathApi_pb2.RetReply(message=f"Err_{str(e)}")

    def Pause(self, request, context):
        # Пауза
        print(f"Pause: {request.modelId}")
        return MathApi_pb2.RetReply(message="Pause успешен")


def serve():
    # Функция запуска gRPC сервера
    port = "5080"

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Добавление сервиса к серверу
    MathApi_pb2_grpc.add_MathApiServicer_to_server(MathApi(), server)

    # Настройка порта
    server.add_insecure_port("[::]:" + port)

    # Выводт информации о запуске
    print(f"СЕРВЕР ЗАПУЩЕН НА ПОРТУ {port}")
    print("Ожидание подключений...")

    # Запуск сервера
    server.start()
    # Ожидание завершения работы
    server.wait_for_termination()


if __name__ == "__main__":
    serve()