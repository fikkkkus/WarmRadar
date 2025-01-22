
class ControllerParams:
    def __init__(self):
        # Инициализация параметров
        self.height = 0.0  # Высота реактора
        self.radius = 0.0   # Радиус реактора
        self.items_and_layers = None  # Пример слоев сырья
        self.thermal_diffusivity = 0.0 # Температуропроводность
        self.time_delta = 0.0  # Время моделирования (сек)
        self.time_steps = 0  # Кол-во шагов моделирования
        self.heat_function = None  # Функция нагрева
        self.heat_source = None  # Точка подвода тепла (r, z, φ)
        self.grid_size = (0.0, 0.0, 0.0)  # Размер сетки (r, z, φ)

    def validate(self):
        """Проверяет параметры и возвращает список ошибок"""
        errors = []

        # Проверки числовых значений
        if self.height <= 0:
            errors.append("Не указана высота.")
        if self.radius <= 0:
            errors.append("Не указан радиус.")
        if self.thermal_diffusivity <= 0:
            errors.append("Не указана температуропроводность.")
        if self.time_delta <= 0:
            errors.append("Не указан временной шаг.")
        if self.time_steps <= 0:
            errors.append("Не указано количество шагов по времени.")
        if any(dim <= 0 for dim in self.grid_size):
            errors.append("Не указана размерность сетки (R, Z, Ф).")

        # Проверки на None
        if self.items_and_layers is None:
            errors.append("Не указаны слои сырья.")
        if self.heat_function is None:
            errors.append("Не указана функция нагрева.")
        # if self.heat_source is None:
        #     errors.append("Не указана точка подвода тепла.")

        return errors
