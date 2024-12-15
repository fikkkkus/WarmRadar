import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
import pyqtgraph as pg

class UI_FunctionChoice(QMainWindow):
    def __init__(self, Form=None):
        super().__init__()

    def setupController(self, Controller):
        self.Controller = Controller

    def setupUi(self, Form):
        """Инициализация интерфейса. Используется объект Form."""
        self.window = Form
        Form.setWindowTitle("График температуры")
        Form.setGeometry(100, 100, 800, 600)

        # Центральный виджет
        self.central_widget = QWidget(Form)
        Form.setCentralWidget(self.central_widget)  # Установка центрального виджета
        layout = QVBoxLayout(self.central_widget)

        # Создание графика
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        # Настройка графика
        self.plot_widget.setLabel('left', 'Температура', units='°C')
        self.plot_widget.setLabel('bottom', 'Шаги времени', units='с')
        self.plot_widget.setYRange(0, 600)
        self.plot_widget.setXRange(0, self.Controller.time_steps)

        # Данные для графика
        self.points = [(0, 500), (self.Controller.time_steps, 500)]  # Начальные точки

        # Элементы графика
        self.line = pg.PlotDataItem([], [], pen=pg.mkPen('r', width=2))
        self.scatter = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(0, 0, 255, 150))
        self.ghost_point = pg.ScatterPlotItem(size=10,
                                              pen=pg.mkPen((200, 200, 200, 150), width=2),
                                              brush=pg.mkBrush(200, 200, 200, 50))

        # Добавление элементов на график
        self.plot_widget.addItem(self.line)
        self.plot_widget.addItem(self.scatter)
        self.plot_widget.addItem(self.ghost_point)

        # Обновление графика
        self.update_plot()

        # Состояние
        self.dragged_point_index = None

        # Подключение событий
        self.scatter.sigClicked.connect(self.on_point_click)
        self.plot_widget.mousePressEvent = self.on_mouse_press
        self.plot_widget.mouseMoveEvent = self.on_mouse_move
        self.plot_widget.mouseReleaseEvent = self.on_mouse_release

        # Кнопка "Продолжить"
        self.startModel = QPushButton("Продолжить", self.central_widget)
        self.startModel.setStyleSheet("""
                    background-color: blue;    /* Синий фон кнопки */
                    color: white;              /* Белый цвет текста */
                    font-size: 16px;           /* Увеличенный размер текста */
                    border-radius: 10px;       /* Закругление краев */
                    padding: 10px 15px;        /* Отступы */
                    margin-top: 8px;
                """)
        self.startModel.clicked.connect(self.continue_)
        layout.addWidget(self.startModel)

    def continue_(self):
        """Завершение работы и сохранение результатов."""
        self.Controller.heat_function = self.points
        print(self.points)
        self.window.close()

    def update_plot(self):
        """Обновляет линии и точки на графике."""
        self.scatter.setData([p[0] for p in self.points], [p[1] for p in self.points], size=10, pen=pg.mkPen('b', width=3))
        self.line.setData([p[0] for p in self.points], [p[1] for p in self.points])

    def on_point_click(self, scatter, points):
        """Обрабатывает нажатие на точку."""
        if points:
            clicked_point = points[0]
            self.dragged_point_index = self.points.index((clicked_point.pos().x(), clicked_point.pos().y()))
            print(f"Точка выбрана: {self.dragged_point_index}")

    def delete_point(self):
        """Удаляет точку, если она выбрана."""
        if self.dragged_point_index is not None:
            del self.points[self.dragged_point_index]
            self.dragged_point_index = None
            self.update_plot()

    def on_mouse_press(self, event):
        """Обрабатывает нажатие кнопки мыши для начала перетаскивания или добавления точки."""
        pos = event.pos()
        scene_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        points = self.scatter.pointsAt(scene_pos)

        if points:
            self.dragged_point_index = self.points.index((points[0].pos().x(), points[0].pos().y()))
            print(f"Точка выбрана: {self.dragged_point_index}")

            if event.button() == Qt.RightButton:
                self.delete_point()
        else:
            if event.button() == Qt.LeftButton:
                if 0 <= scene_pos.x() <= self.Controller.time_steps:
                    self.points.append((scene_pos.x(), self.interpolate_y(scene_pos.x())))
                    self.points.sort(key=lambda point: point[0])
                    self.update_plot()

    def on_mouse_move(self, event):
        """Обрабатывает движение мыши для перемещения точки или отображения призрачной точки."""
        pos = event.pos()
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)

        if self.dragged_point_index is not None:
            self.ghost_point.setData([])

            left_point = self.points[self.dragged_point_index - 1] if self.dragged_point_index > 0 else None
            right_point = self.points[self.dragged_point_index + 1] if self.dragged_point_index < len(self.points) - 1 else None

            new_x = max(0, min(self.Controller.time_steps, round(mouse_point.x(), 1)))
            if left_point:
                new_x = max(new_x, left_point[0])
            if right_point:
                new_x = min(new_x, right_point[0])

            new_y = max(0, min(600, round(mouse_point.y())))

            self.points[self.dragged_point_index] = (new_x, new_y)
            self.points.sort(key=lambda point: point[0])
            self.update_plot()

        else:
            if 0 <= mouse_point.x() <= self.Controller.time_steps:
                x_closest = round(mouse_point.x(), 1)
                y_closest = self.interpolate_y(x_closest)
                self.ghost_point.setData([x_closest], [y_closest])
            else:
                self.ghost_point.setData([])

    def interpolate_y(self, x):
        """Интерполирует y для заданного x."""
        return self.linear_interpolate(x)

    def linear_interpolate(self, x):
        """Линейная интерполяция."""
        left_point = None
        right_point = None
        for i in range(len(self.points) - 1):
            if self.points[i][0] <= x <= self.points[i + 1][0]:
                left_point = self.points[i]
                right_point = self.points[i + 1]
                break

        if left_point and right_point:
            x1, y1 = left_point
            x2, y2 = right_point
            return y1 + (x - x1) * (y2 - y1) / (x2 - x1)
        else:
            return 500

    def on_mouse_release(self, event):
        """Сбрасывает состояние перетаскивания."""
        self.dragged_point_index = None

    def center_window(self):
        """Центрирует окно на экране."""
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.window.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.window.move(window_geometry.topLeft())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    Form = QMainWindow()
    controller = type('Controller', (object,), {'time_steps': 20})()  # Создание тестового контроллера
    window = UI_FunctionChoice()
    window.setupController(controller)
    window.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())