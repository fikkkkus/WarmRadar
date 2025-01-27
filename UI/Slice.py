from tkinter.tix import Form

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyvista as pv
import pyvistaqt as pvqt
from pyvista.plotting.opts import ElementType

from UI.Simulation import ItemWidget


class Ui_Slice(object):
    def setupController(self, Controller):
        self.Controller = Controller

    def setupUi(self, Form):
        self.window = Form
        Form.setObjectName("Form")
        Form.resize(794, 626)

        self.normal = None
        self.origin = None
        self.points_for_slice=None

        # Create group box container
        self.groupBox6 = QtWidgets.QGroupBox(Form)
        self.groupBox6.setGeometry(QtCore.QRect(70, 30, 651, 551))
        self.groupBox6.setStyleSheet(""" 
            #groupBox6 {
                border: 2px solid black;
                border-radius: 100px;
                background-color: white;
            }
        """)
        self.groupBox6.setTitle("")
        self.groupBox6.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox6.setObjectName("groupBox6")

        # Create PyVista plotter widget (background layer)
        self.create_pyvista_plotter() # создаём цилиндр
        self.create_overlay_text_button()

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def create_slice_choicing_plotter(self, R, Z, PHI, Nr, Nz, Nphi, pabana):
        points_for_slice = []
        pl = pvqt.QtInteractor(self.widget_3)

        # Функция для изменения цвета при выборе точки
        def change_color(picked):
            # Получаем координаты выбранной точки
            picked_points = picked.points[0]
            if picked_points is not None and len(picked_points) > 0:
                picked_point = picked_points  # Берем последнюю выбранную точку
                points_for_slice.append(picked_point)
                if len(points_for_slice) == 3:
                    v1 = points_for_slice[1] - points_for_slice[0]
                    v2 = points_for_slice[2] - points_for_slice[0]
                    normal_vector = np.cross(v1, v2)
                    normal_vector_normalized = normal_vector / np.linalg.norm(normal_vector)

                    plane = pv.Plane(center=points_for_slice[0], direction=normal_vector_normalized, i_size=3, j_size=3,
                                     i_resolution=10, j_resolution=10)
                    pl.add_mesh(plane, color="lightblue", opacity=0.5)
                    pl.add_points(np.array([points_for_slice[0], points_for_slice[1], points_for_slice[2]]),
                                  color="blue", point_size=10)

                    self.origin = points_for_slice[0]
                    self.normal = normal_vector_normalized
                    self.points_for_slice=points_for_slice

            else:
                print("Не удалось выбрать точку.")

        # Параметры цилиндра
        dr, dz, dphi = R / (Nr - 1), Z / (Nz - 1), PHI / Nphi
        r = np.linspace(dr, R, Nr - 1)
        z = np.linspace(0, Z, Nz)
        phi = np.linspace(0, PHI, Nphi, endpoint=False)

        R_grid, PHI_grid, Z_grid = np.meshgrid(r, phi, z, indexing="ij")
        X = R_grid * np.cos(PHI_grid)
        Y = R_grid * np.sin(PHI_grid)
        points = np.column_stack((X.ravel(), Y.ravel(), Z_grid.ravel()))
        grid = pv.PolyData(points)

        grid["R"] = R_grid.ravel()
        grid["Phi"] = PHI_grid.ravel()
        grid["Z"] = Z_grid.ravel()

        T = np.zeros((Nr - 1, Nphi, Nz))
        grid["c_values"] = T.ravel()
        indices = np.arange(len(grid.points))
        grid["indices"] = indices

        # Сетку с уменьшенными точками
        cylinder_surface_points_grid = pabana.get_reduced_cylinder_surface_points(
            pabana.get_cylinder_surface_points(grid, R, Z),
            step_r=7, step_phi=2,
            step_z=2)

        # Цилиндр
        cylinder = pv.Cylinder(radius=R, height=Z, resolution=50, center=(0, 0, Z / 2), direction=(0, 0, 1))
        pl.add_mesh(cylinder, color="gray", pickable=False)
        pl.add_mesh(cylinder_surface_points_grid, color="red", point_size=10, pickable=True)

        # Включаем выбор элементов
        pl.enable_element_picking(callback=change_color, mode=ElementType.POINT, pickable_window=True, show_message = False)
        #
        return pl

    def create_pyvista_plotter(self):
        # Create QWidget to embed plotter (cover the entire groupBox6)
        self.widget_3 = QtWidgets.QWidget(self.groupBox6)
        self.widget_3.setGeometry(QtCore.QRect(0, 0, 651, 551))  # Full size of groupBox6
        self.widget_3.setStyleSheet("background-color: transparent;")

        # Apply mask to make the widget have rounded corners
        path = QtGui.QPainterPath()
        path.setFillRule(QtCore.Qt.WindingFill)

        # Convert QRect to QRectF
        rect = QtCore.QRectF(self.widget_3.rect())  # Convert QRect to QRectF
        path.addRoundedRect(rect, 120, 120)  # Setting radius of 100 for the rounded corners
        mask = QtGui.QRegion(path.toFillPolygon().toPolygon())
        self.widget_3.setMask(mask)

        R, Z, PHI = self.Controller.radius, self.Controller.height, 2* np.pi
        Nr, Nz, Nphi =  self.Controller.grid_size[0],  self.Controller.grid_size[1],  self.Controller.grid_size[2]

        self.plotter = self.create_slice_choicing_plotter(R, Z, PHI, Nr, Nz, Nphi,
                                                                         self.reactorSimulation)


        # Set the size of the plotter (smaller than the widget)
        plotter_width = 640  # Set desired width for the plotter
        plotter_height = 540  # Set desired height for the plotter

        # Calculate the position to center the plotter in the widget
        x_pos = (self.widget_3.width() - plotter_width) // 2
        y_pos = (self.widget_3.height() - plotter_height) // 2

        # Set the geometry for the plotter to make it smaller and centered
        self.plotter.setGeometry(QtCore.QRect(x_pos, y_pos, plotter_width, plotter_height))

        # Create PyVista Cylinder mesh
        #cylinder = pv.Cylinder(radius=1, height=2, resolution=50, center=(0, 0, 1), direction=(0, 0, 1))
        #self.plotter.add_mesh(cylinder, color="lightblue", opacity=0.7, show_edges=True)

    def create_overlay_text_button(self):
        # Create label on top of the plotter
        self.label = QtWidgets.QLabel(self.groupBox6)
        self.label.setGeometry(QtCore.QRect(150, 20, 351, 20))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.label.setFont(font)
        self.label.setStyleSheet("""
            background-color: white;
            color: black;
        """)
        self.label.setObjectName("label")

        # Create button on top of the plotter
        self.startModel = QtWidgets.QPushButton(self.groupBox6)
        self.startModel.setGeometry(QtCore.QRect(220, 490, 201, 47))
        self.startModel.setStyleSheet("""
            #startModel {
                background-color: blue;
                color: white;
                font-size: 16px;
                border-radius: 10px;
                padding: 10px 15px;
            }
        """)
        self.startModel.setObjectName("startModel")
        self.startModel.clicked.connect(self.add_new_item)

        self.window.closeEvent = self.closeEvent

    def closeEvent(self, event):
        self.plotter.close()
        event.accept()

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Slice"))
        self.label.setText(_translate("Form", "Выберите 3 точки для построения среза"))
        self.startModel.setText(_translate("Form", "Добавить"))

    def setInsertWidget(self, verticalLayout, widget_2):
        self.widgetInsert = widget_2
        self.layoutInsert = verticalLayout

    def add_new_item(self):
        new_item = ItemWidget(self.normal, self.origin, self.widgetInsert,self.points_for_slice)
        new_item.setupReactorSimulation(self.reactorSimulation)

        self.layoutInsert.insertWidget(0, new_item)
        self.window.close()

    def setupReactor(self, reactorSimulation):
        self.reactorSimulation = reactorSimulation


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_Slice()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
