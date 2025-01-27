import os

import pyvista as pv
import pyvistaqt as pvqt
from PyQt5 import QtCore, QtGui, QtWidgets
import random
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QStackedLayout

import sys

from Data.Calculations import get_current_simulation_number, increment_simulation_number
from Data.DataHadler import DataHandler
from Data.ReactorSimulation import ReactorSimulation

sys.setrecursionlimit(2000)
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)






class ItemWidget(QtWidgets.QPushButton):
    """Класс для создания элемента с изображением и связанным PyVista Mesh."""

    def setupController(self, Controller):
        self.Controller = Controller




    def setupReactorSimulation(self, ReactorSimulation):
        self.reactorSimulation = ReactorSimulation
        self.pyvista_mesh_slice=self.reactorSimulation.get_slice_and_surface_points(self.normal,self.origin)
        self.cylinder=self.reactorSimulation.get_slice_cylinder(self.normal,self.origin)
        self.interpolated = self.cylinder.interpolate(self.pyvista_mesh_slice, radius=0.1)
        self.interpolated.set_active_scalars("c_values")
        self.plotter.add_mesh(self.interpolated, scalars='c_values', opacity=1, cmap='coolwarm',
                                name='interpolated_mesh')


        self.plotterInter.add_mesh(self.interpolated, scalars='c_values', opacity=1, cmap='coolwarm',
                              name='interpolated_mesh')
        self.setNewMesh()

    def __init__(self, normal, origin,parent=None, points_for_slice=None ):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.cylinder=None
        self.pyvista_mesh_slice = None  # Атрибут для хранения связанного PyVista Mesh
        self.interpolated=None
        self.grid_T = None
        self.normal = normal
        self.origin = origin
        self.points_for_slice=points_for_slice

        self.clicked.connect(self.on_click)
        self.plotter = pv.Plotter(off_screen=True)#скриншот

        self.pyvista_window = QtWidgets.QWidget()
        self.plotterInter = pvqt.QtInteractor(self.pyvista_window)# отдельное окно


    def setNewMesh(self):
        #self.pyvista_mesh_slice = self.reactorSimulation.get_slice(self.normal, self.origin)
        #self.setNewMeshForPlotterQT()
        self.newImageForWidget()

    def newImageForWidget(self):
        print("324234")
        #self.plotter.remove_actor("c_m")
        #self.plotter.add_mesh(self.pyvista_mesh_slice, scalars="c_values", cmap="coolwarm", point_size=10,
        #                      render_points_as_spheres=True, name="c_m", show_scalar_bar=False)

        self.grid_T=self.reactorSimulation.get_new_grid()

        self.pyvista_mesh_slice["c_values"] = self.grid_T["c_values"][self.pyvista_mesh_slice["indices"]]
        self.interpolated.point_data['c_values'] = self.cylinder.interpolate(self.pyvista_mesh_slice, radius=0.1)[
            'c_values']
        self.plotter.update_scalars(self.interpolated.point_data['c_values'], render=True)

        #это другой плоттер перенести
        self.plotterInter.update_scalars(self.interpolated.point_data['c_values'], render=True)


        print("234234")
        print(self.points_for_slice)

        self.reactorSimulation.rotate_slice_to_camera(self.plotter, self.points_for_slice)
        image = self.reactorSimulation.plotter_to_qimage(self.plotter)
        qimage = QImage(image[0], image[1], image[2], image[3], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        # Установка иконки на кнопку
        self.setIcon(QIcon(pixmap))

        # Настройка размера иконки, чтобы она соответствовала кнопке
        self.setIconSize(self.size())

    # def setNewMeshForPlotterQT(self):
    #     self.plotterInter.remove_actor("c_m")
    #     self.plotterInter.add_mesh(self.pyvista_mesh_slice, scalars="c_values", cmap="coolwarm",
    #                                point_size=10,
    #                                render_points_as_spheres=True, name="c_m", show_scalar_bar=False)
    def on_click(self):
        """Обработка клика по элементу, открываем окно PyVista."""
        self.show_pyvista_window()

    # окно мини среза
    def show_pyvista_window(self):
        """Создание окна PyVista внутри PyQt при клике на элемент."""
        # Создаем окно с PyVista
        self.pyvista_window.setWindowTitle("PyVista 3D Viewer")
        self.pyvista_window.setGeometry(100, 100, 800, 600)

        # Создаем объект QtInteractor для PyVista
        self.plotterInter.setGeometry(0, 0, 800, 600)

        # Если у элемента есть mesh, используем его
        if self.pyvista_mesh_slice is None:
            # Если Mesh не установлен, по умолчанию создаем сферу
            self.pyvista_mesh_slice = pv.Sphere()

        # Добавляем Mesh в окно PyVista
        # self.plotterInter.add_mesh(self.pyvista_mesh_slice, scalars="c_values", cmap="coolwarm",
        #                            point_size=10,
        #                            render_points_as_spheres=True, name="c_m", show_scalar_bar=False)

        # Показываем окно
        self.pyvista_window.show()

        # Привязываем закрытие окна PyVista к функции очистки ресурсов
        self.pyvista_window.closeEvent = self.close_pyvista_window

    def close_pyvista_window(self, event):
        """Метод, вызываемый при закрытии окна PyVista."""
        # self.plotterInter.disable()
        event.accept()  # Принять событие закрытия

    def change_image(self, new_image_path):
        """Метод для изменения картинки элемента."""
        self.image_path = new_image_path
        self.setStyleSheet(f"""
            border-radius: 20px;
            border: 2px solid #000;
            background-image: url({self.image_path});
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
        """)

    def set_pyvista_mesh(self, mesh):
        """Метод для установки связанного PyVista Mesh."""
        self.pyvista_mesh_slice = mesh

    def get_pyvista_mesh(self):
        """Метод для получения связанного PyVista Mesh."""
        return self.pyvista_mesh_slice

class Ui_Simulation(object):
    def setupController(self, Controller):
        self.Controller = Controller

        self.OUTPUT_FOLDER_JSON = None
        self.OUTPUT_DATA_FOLDER = None
        self.PARAMETERS_FILE = None
        self.CURRENT_DIR = os.path.dirname(__file__)  # Папка, где находится Loading.py



        temp_folder_name = "../Data/calculated_models/" + Controller.simulation_name
        self.OUTPUT_FOLDER_JSON = os.path.join(self.CURRENT_DIR, temp_folder_name)
        self.OUTPUT_DATA_FOLDER = os.path.join(self.OUTPUT_FOLDER_JSON, "output_data")
        print("ggg")
        self.PARAMETERS_FILE = os.path.join(self.OUTPUT_FOLDER_JSON, "model_parameters.json")

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1173, 705)

        # Левый виджет (панель)
        self.widget_2 = QtWidgets.QWidget(Form)
        self.widget_2.setGeometry(QtCore.QRect(0, 0, 341, 701))
        self.widget_2.setObjectName("widget_2")

        self.line_2 = QtWidgets.QFrame(self.widget_2)
        self.line_2.setGeometry(QtCore.QRect(0, 70, 341, 16))
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")

        self.pushButton = QtWidgets.QPushButton(self.widget_2)
        self.pushButton.setGeometry(QtCore.QRect(280, 20, 51, 28))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("+")
        self.pushButton.clicked.connect(self.add_new_item)

        self.label = QtWidgets.QLabel(self.widget_2)
        self.label.setGeometry(QtCore.QRect(100, 20, 61, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setObjectName("label")

        self.scrollArea = QtWidgets.QScrollArea(self.widget_2)
        self.scrollArea.setGeometry(QtCore.QRect(0, 77, 341, 650))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # Виджет внутри ScrollArea
        self.scrollWidget = QtWidgets.QWidget()
        self.scrollArea.setWidget(self.scrollWidget)

        # Вертикальный Layout для элементов
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollWidget)

        # Устанавливаем выравнивание элементов по центру
        self.verticalLayout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        # Правый виджет (PyVista)
        self.widget_3 = QtWidgets.QWidget(Form)
        self.widget_3.setGeometry(QtCore.QRect(340, 0, 831, 701))
        self.widget_3.setObjectName("widget_3")

        self.plotter = pvqt.QtInteractor(self.widget_3)

        self.plotter.setGeometry(0, 0, 831, 701)

        self.data_handler = DataHandler(output_folder=self.OUTPUT_DATA_FOLDER, parameters_file=self.PARAMETERS_FILE)
        # Инициализация симуляции
        self.reactorSimulation = ReactorSimulation(self.data_handler)

        annotations = {
            1: "600",
            0.833: "500",
            0.667: "400",
            0.500: "300",
            0.333: "200",
            0.167: "100",
            0: "0"
        }

        # Добавляем меши в сцену
        self.plotter.add_mesh(self.reactorSimulation.interpolated, scalars="c_values", cmap="coolwarm", point_size=10,
                              render_points_as_spheres=True, name="c_m", show_scalar_bar=False, annotations = annotations)

        self.plotter.add_scalar_bar(
            title="Temperature (°C)",
            label_font_size=12,
            title_font_size=14,
            position_x=0.06,  # смещение по горизонтали (левее)
            position_y=0.11,  # размещение по вертикали
            width=0.1,  # ширина полосы
            height=0.8,  # высота полосы
            vertical=True,
            n_labels=0,
        )

        self.slider_timer = QTimer()
        self.slider_timer.timeout.connect(self.move_slider)
        self.slider_running = False

        self.horizontalSlider = QtWidgets.QSlider(self.widget_3)
        self.horizontalSlider.setGeometry(QtCore.QRect(190, 620, 471, 22))
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setStyleSheet("background: white;")
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.horizontalSlider.setMaximum(self.Controller.time_steps)
        self.horizontalSlider.valueChanged.connect(self.move_slider2)


        self.pushButton3 = QtWidgets.QPushButton(self.widget_3)
        self.pushButton3.setObjectName("pushButton1")
        self.pushButton3.setGeometry(QtCore.QRect(740, 600, 60, 60))
        self.set_play_icon()
        self.pushButton3.setStyleSheet("border : 0; background: white;")
        self.pushButton3.clicked.connect(self.toggle_play_stop)

        self.label_2 = QtWidgets.QLabel(self.widget_3)
        self.label_2.setGeometry(QtCore.QRect(120, 620, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.label_2.setStyleSheet("background: white;")

        self.label_3 = QtWidgets.QLabel(self.widget_3)
        self.label_3.setGeometry(QtCore.QRect(670, 620, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.label_3.setStyleSheet("background: white;")

        self.label_4 = QtWidgets.QLabel(self.widget_3)
        self.label_4.setGeometry(QtCore.QRect(400, 640, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.label_4.setStyleSheet("background: white;")

        self.horizontalSlider.sliderPressed.connect(self.on_slider_pressed)
        self.horizontalSlider.sliderReleased.connect(self.on_slider_released)
        self.user_change = False

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def update_temperature(self, value):
        self.reactorSimulation.update_temperature(value,self.OUTPUT_DATA_FOLDER)
        self.plotter.update_scalars(self.reactorSimulation.interpolated.point_data['c_values'], render=True)

        for i in range(self.verticalLayout.count()):
            item = self.verticalLayout.itemAt(i)
            widget = item.widget()  # Получить виджет, если элемент представляет собой виджет
            widget.setNewMesh()

    def move_slider(self):
        value = self.horizontalSlider.value()
        if value < self.horizontalSlider.maximum():
            self.update_temperature(value + 1)
            self.horizontalSlider.setValue(value + 1)
        else:
            self.slider_timer.stop()
            self.set_play_icon()
            self.slider_running = not self.slider_running

    def move_slider2(self):
        if self.user_change:
            value = self.horizontalSlider.value()
            if value < self.horizontalSlider.maximum():
                self.update_temperature(value + 1)

    def on_slider_pressed(self):
        # Устанавливаем флаг, что пользователь начал изменять слайдер
        self.user_change = True

    def on_slider_released(self):
        # Сбрасываем флаг, когда пользователь отпускает слайдер
        self.user_change = False

    def set_play_icon(self):
        current_dir = os.path.dirname(__file__)  # Папка, где находится Loading.py
        image_path = os.path.join(current_dir, "../images/play.png")
        pixmap = QtGui.QPixmap(image_path)
        self.pushButton3.setIcon(QtGui.QIcon(pixmap))
        self.pushButton3.setIconSize(QtCore.QSize(60, 60))

    def set_stop_icon(self):
        current_dir = os.path.dirname(__file__)  # Папка, где находится Loading.py
        image_path = os.path.join(current_dir, "../images/stop.png")
        pixmap = QtGui.QPixmap(image_path)
        self.pushButton3.setIcon(QtGui.QIcon(pixmap))
        self.pushButton3.setIconSize(QtCore.QSize(60, 60))

    def toggle_play_stop(self):
        if self.slider_running:
            self.slider_timer.stop()
            self.set_play_icon()
        else:
            self.slider_timer.start(100)
            self.set_stop_icon()
        self.slider_running = not self.slider_running

    def add_new_item(self):
        """Добавление нового элемента в начало списка."""

        # Создание главного окна
        self.sliceWindow = QtWidgets.QMainWindow()
        print(f"add_new_item")
        try:
            # Импорт UI
            from UI.Slice import Ui_Slice

            # Создание экземпляра интерфейса
            self.ui = Ui_Slice()

            # Настройка виджетов и контроллера
            self.ui.setInsertWidget(self.verticalLayout, self.widget_2)

            self.ui.setupController(self.Controller)
            self.ui.setupReactor(self.reactorSimulation)
            self.ui.setupUi(self.sliceWindow)
            # Показ окна
            self.sliceWindow.show()
            print("end add_new_item")

        except Exception as e:
            print(f"add_new_item: ошибка при выполнении - {e}")

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Simulation"))
        self.pushButton.setText(_translate("Form", "+"))
        self.label.setText(_translate("Form", "Срезы"))
        self.label_2.setText(_translate("Form", "00:00"))
        self.label_3.setText(_translate("Form", "00:00"))
        self.label_4.setText(_translate("Form", "00:00"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_Simulation()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())