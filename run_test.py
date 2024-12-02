import serial.tools.list_ports



def list_usb_devices_with_arduino_check():
    """
    Lists all connected USB devices, identifies Arduino devices, 
    and explicitly marks non-Arduino devices.
    """
    arduinos = []
    non_arduinos = []
    ports = serial.tools.list_ports.comports()

    # Known Arduino Vendor/Product IDs (as strings)
    arduino_ids = [
        {"vendor_id": "0x2341", "product_id": "0x0043"},  # Arduino Uno (official)
        {"vendor_id": "0x2341", "product_id": "0x0243"},  # Arduino Uno (clone)
        {"vendor_id": "0x1A86", "product_id": "0x7523"},  # CH340 (common clone)
        {"vendor_id": "0x0403", "product_id": "0x6001"},  # FTDI
    ]

    for port in ports:
        # Convert port VID and PID to hexadecimal strings for comparison
        port_vid = f"0x{port.vid:04x}" if port.vid else None
        port_pid = f"0x{port.pid:04x}" if port.pid else None

        is_arduino = any(
            port_vid == arduino_id["vendor_id"] and port_pid == arduino_id["product_id"]
            for arduino_id in arduino_ids
        )

        if is_arduino:
            arduinos.append({
                "device": port.device,
                "name": port.description,
                "vendor_id": port_vid,
                "product_id": port_pid,
            })
        else:
            non_arduinos.append({
                "device": port.device,
                "name": port.description,
                "vendor_id": port_vid,
                "product_id": port_pid,
            })

    if arduinos:
        print("Connected Arduino devices:")
        for arduino in arduinos:
            print(f"Device: {arduino['device']}, Name: {arduino['name']}, VID: {arduino['vendor_id']}, PID: {arduino['product_id']}")
    else:
        print("No Arduino devices found. Please ensure your devices are connected and properly configured.")

    if non_arduinos:
        print("\nOther connected USB devices (not Arduinos):")
        for device in non_arduinos:
            print(f"Device: {device['device']}, Name: {device['name']}, VID: {device['vendor_id']}, PID: {device['product_id']}")

    return arduinos, non_arduinos

list_usb_devices_with_arduino_check()