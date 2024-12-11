import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QComboBox, QMessageBox, QFrame, QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt
import time
import serial
from pyqtgraph import PlotWidget
from pyqtgraph import TextItem


class Motor:
    """Represents a single motor and its operations."""
    def __init__(self, name, port, axis):
        self.name = name
        self.port = port
        self.axis = axis
        self.arduino = None
        self.current_position = 0

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
        self.send_command(f"G0{self.axis}{steps}")
        self.current_position += steps

    def set_home(self):
        self.send_command(f"G92{self.axis}0")


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
        self.num_arduinos_spinner.setMinimum(1)
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
        """Completely clears the Arduino configuration area, removing all widgets and resetting the layout."""
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

        # Open Motor Config Window
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
        self.motor_positions = []
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Display each Arduino with checkboxes for motors
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

        # Set Configuration Button
        self.button_layout = QHBoxLayout()
        self.set_config_button = QPushButton("Set Motors and Graph")
        self.set_config_button.clicked.connect(self.set_motor_configuration)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.set_config_button)
        self.button_layout.addStretch()

        self.main_layout.addLayout(self.button_layout)

    def set_motor_configuration(self):
        # Initialize motors based on selection
        self.motors = []
        for port, motor_checkboxes in self.selected_motors.items():
            for axis, checkbox in motor_checkboxes.items():
                if checkbox.isChecked():
                    motor = Motor(f"{port} - {axis}", port, axis)
                    self.motors.append(motor)

        # Show the graph
        self.graph_window = MotorGraph(self.motors)
        self.graph_window.show()
        self.close()


class MotorGraph(QMainWindow):
    def __init__(self, motors):
        super().__init__()
        self.setWindowTitle("Motor Positions Graph")
        self.setGeometry(300, 150, 800, 600)

        self.motors = motors
        self.motor_positions = {motor.name: motor.current_position for motor in self.motors}
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Create graph
        self.graph = PlotWidget()
        self.graph.setLabel('left', 'Position')
        self.graph.setLabel('bottom', 'Motor')
        self.graph.setYRange(0, 100)
        self.graph.setXRange(0, len(self.motors) + 1)
        self.main_layout.addWidget(self.graph)

        # Input for steps to move motors
        self.steps_label = QLabel("Enter number of steps for motors:")
        self.steps_input = QLineEdit(self)
        self.steps_input.setPlaceholderText("Enter steps, comma separated")
        self.move_button = QPushButton("Move Motors")
        self.move_button.clicked.connect(self.move_motors)

        self.main_layout.addWidget(self.steps_label)
        self.main_layout.addWidget(self.steps_input)
        self.main_layout.addWidget(self.move_button)

        # Display the initial graph
        self.update_graph()

    def move_motors(self):
        steps_input = self.steps_input.text()
        try:
            steps = list(map(int, steps_input.split(",")))
            if len(steps) != len(self.motors):
                QMessageBox.warning(self, "Error", "Number of steps does not match number of motors.")
                return
            for motor, step in zip(self.motors, steps):
                motor.move(step)

            self.update_graph()
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid steps input. Please enter valid integers.")

    def update_graph(self):
        motor_names = [motor.name for motor in self.motors]
        motor_positions = [motor.current_position for motor in self.motors]

        # Generate numeric x-values for the plot
        motor_indices = list(range(len(self.motors)))

        self.graph.clear()

        # Plot the motor positions
        self.graph.plot(motor_indices, motor_positions, pen="g", symbol='o')

        # Add labels to the graph using TextItem
        plot_item = self.graph.getPlotItem()  # Access the PlotItem from PlotWidget
        for i, name in enumerate(motor_names):
            # Create TextItem
            text = TextItem(name, anchor=(0.5, 0.5))
            text.setPos(motor_indices[i], motor_positions[i])
            text.setColor("black")
            plot_item.addItem(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    configurator = ArduinoConfigurator()
    configurator.show()
    sys.exit(app.exec_())
