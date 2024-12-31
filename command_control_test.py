import serial
import time
import inspect

class SSZ9700CameraController:

    # MARK: __init__()
    def __init__(self, port="COM14", baudrate=9600, timeout=1):
        """ Initialize the camera controller.
        """
        self.serial_port = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
            )


    # MARK: calculate_bcc()
    def calculate_bcc(self, did, mode, sid, stx, payload, etx):
        """ Calculate Block Check Character (BCC) for the command packet.

        Args:
            did (_type_): Destination ID byte
            mode (_type_): Mode byte
            sid (_type_): Sender ID byte
            stx (_type_): Start of Text byte
            payload (_type_): Command payload bytes
            etx (_type_): End of Text byte
        """   
        data = did + mode + sid + stx + payload + etx
        bcc = 0
        for byte in data:
            bcc ^= byte
        return bytes([bcc])


    # MARK: send_command()
    def send_command(self, destination_id, payload):
        """ Send a command packet to the camera and read the response.
        """
        soh  = b'\x01'  # Start of Header
        mode = b'\x81'  # No ACK/NAK
        sid  = b'\x20'  # Sender ID
        stx  = b'\x02'  # Start of Text
        etx  = b'\x03'  # End of Text
       
        bcc = self.calculate_bcc(destination_id, mode, sid, stx, payload, etx)
        print(f"send_command() > bcc: {bcc}")

        command_packet = soh + destination_id + mode + sid + stx + payload + etx + bcc
        print(f"send_command() > command_packet: {command_packet.hex()}")

        serial_response = self.serial_port.write(command_packet)
        print(f"send_command() > serial_response: {serial_response}")

        # Wait briefly and read the response
        time.sleep(0.1)
        response = self.serial_port.read(100)
        print(f"send_command() > response: {response}")

        retry_limit = 5
        retries = 0

        while retries < retry_limit:
            try:
                if response and response[0] == 0x06:  # ACK
                    print("send_command() > while: ACK received.")
                    break
                elif response and response[0] == 0x15:  # NAK
                    print("send_command() > while: NAK received.")
                    break
                else:
                    print("send_command() > while: Unknown Response.  Retrying...")
            
            except Exception as e:
                print(f"send_command() > while: Exception: {e}")

            time.sleep(1)
            retries += 1
            response = self.serial_port.read(100)  # Adjust the length as necessary
            print(f"send_command() > while > response: {response}")
        else:
            print("send_command() > else > Timeout: No response from camera.")               

        return response
    

    # MARK: get_zoom_position()
    def get_zoom_position(self, destination_id):
        """
        Request the current zoom position of the camera.
        """
        # Construct the payload for zoom position
        # payload = b'\x43\x00\x00\x00\x00\x00'
        payload = b'\x43\x30\x30\x30\x30\x30'  # Include valid command

        # Send the command
        response = self.send_command(destination_id, payload)

        # Handle the ACK/NAK response
        if response and response[0] == 0x06:  # ACK received
            print("get_zoom_position() > response: ACK received. Waiting for status...")
            # time.sleep(0.01)  # Wait 2–10 milliseconds for the status
            status_response = self.serial_port.read(100)  # Read the actual zoom position response
            print(f"get_zoom_position() > Status Response: {status_response.hex() if status_response else 'No status received'}")

            # Parse the zoom position from the status response
            zoom_position = self.parse_zoom_position(status_response)
            if zoom_position is not None:
                print(f"get_zoom_position() > zoom_position: Current Zoom Position: {zoom_position}")
            else:
                print("Failed to parse zoom position.")
        elif response and response[0] == 0x15:  # NAK received
            print("get_zoom_position() > response: NAK received. Command failed.")
        else:
            print("get_zoom_position() > response: No valid response received.")


    # MARK: parse_zoom_position()
    def parse_zoom_position(self, response):
        """
        Parse the zoom position from the camera's status response.

        :param response: The response bytes from the camera.
        :return: Zoom position as an integer.
        """
        if len(response) >= 5:
            # Extract the first 4 bytes (ASCII nibbles) and convert to integer
            position_ascii = response[:4].decode('ascii')
            return int(position_ascii, 16)  # Convert from hexadecimal
        else:
            print("parse_zoom_position(): Invalid response length for zoom position.")
            return None


    # MARK: close()
    def close(self):
        """ Close the serial connection. 
        """
        self.serial_port.close()


# MARK: MAIN()
if __name__ == "__main__":
    try:
        # Communication Port
        camera = SSZ9700CameraController(port="COM14", baudrate=9600)

        print()

        # Destination ID
        response = camera.get_zoom_position(destination_id=b'\x31')
        print(f"[Main] Zoom Position Response: {response}")

        camera.close()

        print()
        
    except Exception as e:
        print(f"Error: {e}")

