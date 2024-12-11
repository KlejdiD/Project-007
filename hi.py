import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QComboBox, QMessageBox, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtGui import QPainter
import time
import serial

class Motor:
    """Represents a single motor and its operations."""
    def __init__(self, name, port, axis):
        self.name = name
        self.port = port
        self.axis = axis
        self.steps = 0  # Initial step position
        self.arduino = None

    def connect(self):
        if self.arduino is None or not self.arduino.is_open:
            self.arduino = serial.Serial(self.port, 115200)
            time.sleep(2)

    def disconnect(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.close()

    def send_command(self, command):
        self.connect()
        self.arduino.write(str.encode(f"{command}") + b'\n')
        time.sleep(0.1)

    def move(self, steps):
        self.steps += steps  # Update steps
        self.send_command(f"G0{self.axis}{steps}")  # Send command to motor

    def set_home(self):
        self.steps = 0
        self.send_command(f"G92{self.axis}0")

    def home(self):
        self.send_command(f"G0{self.axis}0")


class ArduinoConfigurator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino Configurator")
        self.setGeometry(300, 150, 800, 600)

        self.num_arduinos = 0
        self.arduino_widgets = []
        self.com_ports = []
        self.arduino_configs = []

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Top row: Arduino count
        self.top_row_frame = QFrame(self)
        self.top_row_frame.setFixedHeight(80)
        self.top_row_layout = QHBoxLayout(self.top_row_frame)

        self.num_arduinos_label = QLabel("Number of Arduinos:")
        self.num_arduinos_spinner = QSpinBox()
        self.num_arduinos_spinner.setMinimum(0)
        self.num_arduinos_spinner.setMaximum(10)

        self.top_row_layout.addWidget(self.num_arduinos_label)
        self.top_row_layout.addWidget(self.num_arduinos_spinner)
        self.main_layout.addWidget(self.top_row_frame)

        # Middle row: Arduino configuration
        self.arduino_frame = QFrame(self)
        self.arduino_frame.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.arduino_layout = QVBoxLayout(self.arduino_frame)
        self.main_layout.addWidget(self.arduino_frame)

        # Bottom row: Buttons
        self.bottom_row_frame = QFrame(self)
        self.bottom_row_frame.setFixedHeight(80)
        self.bottom_row_layout = QHBoxLayout(self.bottom_row_frame)

        self.set_arduino_button = QPushButton("Set Arduino Count")
        self.set_arduino_button.clicked.connect(self.reset_arduino_inputs)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.open_motor_config)

        self.bottom_row_layout.addStretch()
        self.bottom_row_layout.addWidget(self.set_arduino_button)
        self.bottom_row_layout.addWidget(self.next_button)
        self.bottom_row_layout.addStretch()

        self.main_layout.addWidget(self.bottom_row_frame)

    def reset_arduino_inputs(self):
        self.num_arduinos = self.num_arduinos_spinner.value()
        self.clear_arduino_widgets()

        if self.num_arduinos > 0:
            self.update_arduino_inputs()

    def clear_arduino_widgets(self):
        while self.arduino_layout.count() > 0:
            item = self.arduino_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.arduino_widgets.clear()

    def update_arduino_inputs(self):
        self.com_ports = self.scan_com_ports()

        for i in range(self.num_arduinos):
            row_layout = QHBoxLayout()

            label = QLabel(f"Arduino {i + 1}:")
            combo_box = QComboBox()
            combo_box.addItem("Not Assigned")
            combo_box.addItems(self.com_ports)

            row_layout.addWidget(label)
            row_layout.addWidget(combo_box)

            container_widget = QWidget()
            container_widget.setLayout(row_layout)

            self.arduino_layout.addWidget(container_widget)
            self.arduino_widgets.append((label, combo_box))

    def scan_com_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_motor_config(self):
        self.arduino_configs = []

        for label, combo_box in self.arduino_widgets:
            selected_port = combo_box.currentText()
            if selected_port != "Not Assigned":
                self.arduino_configs.append(selected_port)

        if not self.arduino_configs:
            QMessageBox.warning(self, "Warning", "No Arduinos assigned! Using mock data for testing.")
            self.arduino_configs = ["COM_TEST_1", "COM_TEST_2"]

        self.motor_config_window = MotorConfigurator(self.arduino_configs)
        self.motor_config_window.show()
        self.close()


class MotorConfigurator(QMainWindow):
    def __init__(self, arduino_configs):
        super().__init__()
        self.setWindowTitle("Motor Configurator")
        self.setGeometry(300, 150, 800, 600)

        self.arduino_configs = arduino_configs
        self.selected_motors = {}
        self.motor_objects = {}  # To store Motor instances
        self.graph_data = {}
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Create motor configuration interface
        for port in self.arduino_configs:
            group_frame = QFrame(self)
            group_frame.setStyleSheet("border: 1px solid #ccc; background-color: #e9f7ff; margin-bottom: 10px;")
            group_layout = QVBoxLayout(group_frame)

            label = QLabel(f"Arduino ({port}):")
            label.setStyleSheet("font-weight: bold;")
            group_layout.addWidget(label)

            motor_checkboxes = {}
            for axis in ["X", "Y", "Z"]:
                checkbox = QCheckBox(f"Motor ({axis})")
                motor_checkboxes[axis] = checkbox
                group_layout.addWidget(checkbox)

            self.selected_motors[port] = motor_checkboxes
            self.main_layout.addWidget(group_frame)

        # Input for steps to move motors
        self.step_input = QSpinBox()
        self.step_input.setMinimum(-40)
        self.step_input.setMaximum(40)
        self.step_input.setValue(0)  # Default to 0
        self.main_layout.addWidget(QLabel("Input steps for motor movement:"))
        self.main_layout.addWidget(self.step_input)

        # Move Motors Button
        self.move_button = QPushButton("Move Motors")
        self.move_button.clicked.connect(self.move_motors)
        self.main_layout.addWidget(self.move_button)

        # Create Graph to visualize motor movements
        self.chart = QChart()
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.main_layout.addWidget(self.chart_view)

    def move_motors(self):
        steps = self.step_input.value()

        for port, motor_checkboxes in self.selected_motors.items():
            for axis, checkbox in motor_checkboxes.items():
                if checkbox.isChecked():
                    motor_name = f"Motor {axis} ({port})"
                    if motor_name not in self.motor_objects:
                        self.motor_objects[motor_name] = Motor(motor_name, port, axis)

                    motor = self.motor_objects[motor_name]
                    motor.move(steps)
                    self.update_graph(motor)

    def update_graph(self, motor):
        if motor.name not in self.graph_data:
            self.graph_data[motor.name] = []

        # Add new data for graph visualization
        self.graph_data[motor.name].append(motor.steps)

        # Create series for each motor
        series = QLineSeries()
        for i, step in enumerate(self.graph_data[motor.name]):
            series.append(i, step)

        self.chart.addSeries(series)
        self.chart.createDefaultAxes()
        self.chart.setTitle(f"Motor Movement: {motor.name}")

        self.chart_view.repaint()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    configurator = ArduinoConfigurator()
    configurator.show()
    sys.exit(app.exec_())
