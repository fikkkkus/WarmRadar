import matplotlib.pyplot as plt
import pandas as pd


class TGA:
    @staticmethod
    def plot_graph(file_path, x_col, y_col):
        # Читаем файл, пропуская строки с метаданными
        with open(file_path, "r", encoding="cp1251") as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if line.startswith("##"):  # Начало заголовка таблицы
                    header = line[2:].strip().split(";")  # Убираем ## и разбиваем по ";"
                    data_lines = lines[i + 1:]
                    break

        # Создание DataFrame с обработкой пустых значений
        data = []
        for line in data_lines:
            values = [x.strip().replace(",", ".") for x in line.strip().split(";")]
            try:
                data.append([float(v) if v else None for v in values])  # Заменяем пустые значения на None
            except ValueError:
                print(f"Ошибка в строке: {line}")  # Для отладки

        df = pd.DataFrame(data, columns=header)

        # Построение графика
        plt.figure(figsize=(10, 5))
        plt.plot(df[x_col], df[y_col], marker="o", linestyle="-", label=f"{y_col} от {x_col}")
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.title(f"График зависимости {y_col} от {x_col}")
        plt.legend()
        plt.grid()
        return plt
