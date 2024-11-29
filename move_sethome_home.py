import serial
import time

#example commit 
class Motor:
    """Represents a single motor and its operations."""
    def __init__(self, name, port, axis):
        self.name = name
        self.port = port
        self.axis = axis
        self.arduino = None

    def connect(self):
        """Open a serial connection to the motor."""
        if self.arduino is None or not self.arduino.is_open:
            self.arduino = serial.Serial(self.port, 115200)
            time.sleep(2)  # Allow time for the connection to initialize

    def disconnect(self):
        """Close the serial connection."""
        if self.arduino and self.arduino.is_open:
            self.arduino.close()

    def send_command(self, command):
        """Send a raw command to the motor."""
        self.connect()
        self.arduino.write(str.encode("\r\n\r\n"))  # GRBL wake-up sequence
        self.arduino.write(str.encode(f"{command}") + b'\n')
        time.sleep(0.1)  # Allow time for the command to process


    def move(self, steps):
        """Move the motor by the specified number of steps."""
        command_set_system = "$J=G21G90"
        move_command = f"G0{self.axis}{steps}"
        self.send_command(command_set_system)
        self.send_command(move_command)
        return print( f"{self.name} has moved {steps}")

    def set_home(self):
        """Set the current position of the motor as home."""
        command_set_system = "$J=G21G90"
        command_set_home = f"G92{self.axis}0"
        self.send_command(command_set_system)
        self.send_command(command_set_home)
        return print("Home set")

    def home(self):
        """Move the motor to its home position."""
        command_set_system = "$J=G21G90"
        command_move_home = f"G0{self.axis}0"
        self.send_command(command_set_system)
        self.send_command(command_move_home)
        return print(f"{self.name} moved home")

    def __del__(self):
        """Ensure the connection is closed when the object is deleted."""
        self.disconnect()
        return print(f"disconnected {self.name}")


class MotorController:
    """Manages multiple motors."""
    def __init__(self, motors_config):
        self.motors = [Motor(m["name"], m["port"], m["axis"]) for m in motors_config]

    def get_motor(self, motor_name):
        """Retrieve a motor by its name."""
        return next((motor for motor in self.motors if motor.name == motor_name), None)

    def move_motor(self, motor_name, steps):
        """Move a specific motor by name."""
        motor = self.get_motor(motor_name)
        if motor:
            return motor.move(steps)
        else:
            return f"Error: Motor {motor_name} not found."

    def home_motor(self, motor_name):
        """Home a specific motor by name."""
        motor = self.get_motor(motor_name)
        if motor:
            return motor.home()
        else:
            return f"Error: Motor {motor_name} not found."

    def set_motor_home(self, motor_name):
        """Set the home position for a specific motor."""
        motor = self.get_motor(motor_name)
        if motor:
            return motor.set_home()
        else:
            return f"Error: Motor {motor_name} not found."


# Example Usage
if __name__ == "__main__":
    # Configuration for motors
    motors_config = [
        {"name": "motor_1", "port": "COM6", "axis": "X"},
        {"name": "motor_2", "port": "COM3", "axis": "X"},
        {"name": "motor_3", "port": "COM3", "axis": "Y"},
        {"name": "motor_4", "port": "COM3", "axis": "Z"},
        {"name": "motor_5", "port": "COM4", "axis": "X"},
        {"name": "motor_6", "port": "COM4", "axis": "Y"},
        {"name": "motor_7", "port": "COM4", "axis": "Z"},
        {"name": "motor_8", "port": "COM5", "axis": "X"},
        {"name": "motor_9", "port": "COM5", "axis": "Y"},
        {"name": "motor_10", "port": "COM5", "axis": "Z"},
    ]

    # Create a MotorController instance
    controller = MotorController(motors_config)

    # Example operations

    controller.set_motor_home("motor_4")
    time.sleep(5)

    controller.move_motor("motor_6", steps=6)
    time.sleep(5)


    controller.move_motor("motor_4", 7)
    time.sleep(5)
    controller.home_motor("motor_4")
    time.sleep(5)

    controller.set_motor_home("motor_6")
    time.sleep(5)

    controller.move_motor("motor_6", steps=4)
    time.sleep(5)

    controller.home_motor("motor_6")



