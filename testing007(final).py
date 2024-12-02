import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox, QWidget, QSpinBox, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer
from pyqtgraph import PlotWidget
import serial
import os


class Motor:
    """Represents a single motor and its operations."""
    def __init__(self, name, port, axis, position_file="motor_positions.json"):
        self.name = name
        self.port = port
        self.axis = axis
        self.current_position = 0
        self.max_position = 40  # Maximum position limit
        self.target_position = 0
        self.is_moving = False
        self.position_file = position_file

        self.load_position()

    def move(self, steps):
        """Simulate moving the motor."""
        if self.current_position + steps > self.max_position:
            steps = self.max_position - self.current_position
        elif self.current_position + steps < 0:
            steps = -self.current_position

        self.target_position = self.current_position + steps
        self.is_moving = True
        print(f"{self.name} moving to position {self.target_position}")

    def update_position(self):
        """Update motor position step by step."""
        if self.is_moving:
            if self.current_position < self.target_position:
                self.current_position += 1
            elif self.current_position > self.target_position:
                self.current_position -= 1

            if self.current_position == self.target_position:
                self.is_moving = False
                self.save_position()

    def set_home(self):
        """Set the motor's current position as home."""
        self.current_position = 0
        self.target_position = 0
        self.is_moving = False
        print(f"{self.name} set to home position.")
        self.save_position()

    def save_position(self):
        """Save motor position to a file."""
        with open(self.position_file, "a") as file:
            file.write(f"{self.name}: {self.current_position}\n")
        print(f"{self.name} position saved: {self.current_position}")

    def load_position(self):
        """Load motor position from a file."""
        if os.path.exists(self.position_file):
            with open(self.position_file, "r") as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith(self.name):
                        self.current_position = int(line.split(":")[1].strip())
                        self.target_position = self.current_position
                        print(f"{self.name} position loaded: {self.current_position}")


class MotorController:
    """Manages multiple motors."""
    def __init__(self):
        self.motors = []

    def add_motor(self, name, port, axis):
        motor = Motor(name, port, axis)
        self.motors.append(motor)

    def move_multiple_motors(self, motor_steps):
        """Move multiple motors based on a dictionary of steps."""
        for motor_name, steps in motor_steps.items():
            motor = next((m for m in self.motors if m.name == motor_name), None)
            if motor:
                motor.move(steps)


class MotorControlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = MotorController()
        self.motor_positions = []  # Custom positions for motors on the graph
        self.arduino_configs = []  # Stores number of motors for each Arduino
        self.initUI()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_motor_positions)
        self.update_timer.start(100)  # Update every 100ms

    def initUI(self):
        self.setWindowTitle("Motor Control GUI")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Arduino Configuration
        config_layout = QHBoxLayout()
        self.arduino_count_input = QSpinBox()
        self.arduino_count_input.setRange(1, 10)
        config_layout.addWidget(QLabel("Number of Arduinos:"))
        config_layout.addWidget(self.arduino_count_input)

        set_arduinos_button = QPushButton("Set Arduinos")
        set_arduinos_button.clicked.connect(self.set_arduino_configuration)
        config_layout.addWidget(set_arduinos_button)

        main_layout.addLayout(config_layout)

        # Motor Control Area
        self.motor_control_layout = QGridLayout()
        self.motor_checkboxes = []
        self.motor_inputs = []
        self.update_motor_controls()
        main_layout.addLayout(self.motor_control_layout)

        # Graph
        self.graph = PlotWidget()
        self.graph.setLabel('left', 'Position')
        self.graph.setLabel('bottom', 'Motor')
        self.graph.setYRange(0,20)
        self.graph.setXRange(0, 10)  # Default initial range
        self.graph.setMouseEnabled(x=False, y=False)
        main_layout.addWidget(self.graph)

        # Buttons for operations
        button_layout = QHBoxLayout()
        move_button = QPushButton("Move Selected Motors")
        move_button.clicked.connect(self.move_selected_motors)
        button_layout.addWidget(move_button)

        home_button = QPushButton("Set Selected Motors Home")
        home_button.clicked.connect(self.home_selected_motors)
        button_layout.addWidget(home_button)

        main_layout.addLayout(button_layout)

        # Option to manually set motor positions
        position_layout = QHBoxLayout()
        self.custom_position_input = QLineEdit()
        self.custom_position_input.setPlaceholderText("Enter positions (comma-separated)")
        position_button = QPushButton("Set Motor Positions")
        position_button.clicked.connect(self.set_motor_positions)
        position_layout.addWidget(self.custom_position_input)
        position_layout.addWidget(position_button)
        main_layout.addLayout(position_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def set_arduino_configuration(self):
        """Prompt the user to input the number of motors for each Arduino."""
        try:
            num_arduinos = self.arduino_count_input.value()
            self.arduino_configs = []

            for i in range(1, num_arduinos + 1):
                motors_count, ok = self.get_integer_input(f"Number of Motors for Arduino {i}")
                if not ok:
                    QMessageBox.warning(self, "Error", f"Invalid input for Arduino {i}. Please try again.")
                    return
                self.arduino_configs.append(motors_count)

            self.generate_motors()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def generate_motors(self):
        """Generate motors dynamically based on Arduino configuration."""
        self.controller.motors.clear()
        motor_count = 0

        for i, motor_count in enumerate(self.arduino_configs, start=1):
            for j in range(1, motor_count + 1):
                motor_name = f"Arduino {i} Motor {j}"
                self.controller.add_motor(motor_name, f"COM{i}", "X")

        self.update_motor_controls()
        self.auto_distribute_positions()
        self.update_graph()

    def get_integer_input(self, message):
        """Helper to get integer input via dialog."""
        num, ok = QInputDialog.getInt(self, "Input Required", message, min=1, max=10)
        return num, ok

    def update_motor_controls(self):
        """Update the motor controls UI."""
        for i in reversed(range(self.motor_control_layout.count())):
            self.motor_control_layout.itemAt(i).widget().setParent(None)

        self.motor_checkboxes = []
        self.motor_inputs = []

        for i, motor in enumerate(self.controller.motors):
            checkbox = QCheckBox(motor.name)
            self.motor_checkboxes.append(checkbox)
            self.motor_control_layout.addWidget(checkbox, i, 0)

            input_box = QLineEdit()
            input_box.setPlaceholderText("Move steps")
            self.motor_inputs.append(input_box)
            self.motor_control_layout.addWidget(input_box, i, 1)

    def auto_distribute_positions(self):
        """Distribute motor positions evenly if not set manually."""
        num_motors = len(self.controller.motors)
        self.motor_positions = list(range(1, num_motors + 1))

    def move_selected_motors(self):
        """Move selected motors."""
        motor_steps = {}
        for checkbox, input_box, motor in zip(self.motor_checkboxes, self.motor_inputs, self.controller.motors):
            if checkbox.isChecked():
                try:
                    steps = int(input_box.text())
                    motor_steps[motor.name] = steps
                except ValueError:
                    pass  # Ignore invalid inputs

        self.controller.move_multiple_motors(motor_steps)
        self.update_graph()

    def home_selected_motors(self):
        """Set selected motors to home position."""
        for checkbox, motor in zip(self.motor_checkboxes, self.controller.motors):
            if checkbox.isChecked():
                motor.set_home()
        self.update_graph()

    def set_motor_positions(self):
        """Manually set motor positions."""
        try:
            positions = list(map(int, self.custom_position_input.text().split(",")))
            if len(positions) != len(self.controller.motors):
                QMessageBox.warning(self, "Error", "Number of positions does not match number of motors.")
                return

            for motor, pos in zip(self.controller.motors, positions):
                motor.current_position = pos
                motor.target_position = pos
                motor.save_position()

            self.update_graph()
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid positions format. Please use integers separated by commas.")

    def update_motor_positions(self):
        """Update all motor positions."""
        for motor in self.controller.motors:
            motor.update_position()

        self.update_graph()

    def update_graph(self):
        """Update the graph to show motor positions."""
        positions = [motor.current_position for motor in self.controller.motors]
        self.graph.clear()
        self.graph.plot(self.motor_positions, positions, pen="g", name="Motor Positions", symbol='o')

        x_axis = self.graph.getAxis('bottom')
        x_axis.setTicks([[(i, motor.name) for i, motor in enumerate(self.controller.motors)]])
        self.graph.setXRange(0, max(len(self.controller.motors), 10))


# Main Function
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MotorControlGUI()
    gui.show()
    sys.exit(app.exec_())
