"""Controls devices meant for the Magic Home smartphone app.

Quick start::

    light_bulb = MagicHomeDevice(
        device_ip="192.169.176.12", 
        device_type=1, 
        keep_alive=True
        )

    light_bulb.turn_on() # turn on

    light_bulb.change_color(255, 0, 255) # change color to pink

    light_bulb.get_status(return_debug_info=True) # return current light status

    light_bulb.turn_off() # turn off

Common Errors:
- Passing cold and warm white values in change_color() simultaneously will raise a ValueError
- Passing any white and a color value will also raise a ValueError
- Passing a preset number and a preset name simultaneously in send_preset(), 
even if they refer to the same one, will raise a ValueError
"""

import socket
import struct
import datetime
from typing import Literal


class MagicHomeDevice:
    """Represents a Magic Home device."""

    PRESETS = {"rainbow_fade": 37, 
                    "r_b": 38, "g_b": 39, "b_b": 40, "y_b": 41, "lb_b": 42, "m_b": 43, "w_b": 44, "r+g_b": 45, "r+b_b": 46, "g+b_b": 47, 
                    "rainbow_fl": 48, "r_fl": 49, "g_fl": 50, "b_fl": 51, "y_fl": 52, "lb_fl": 53, "m_fl": 54, "w_fl": 55, 
                    "rainbow_c": 56}

    PRESETS_REV = {37: "rainbow_fade", 
            38: "r_b", 39: "g_b", 40: "b_b", 41: "y_b", 42: "lb_b", 43: "m_b", 44: "w_b", 45: "r+g_b", 46: "r+b_b", 47: "g+b_b", 
            48: "rainbow_fl", 49: "r_fl", 50: "g_fl", 51: "b_fl", 52: "y_fl", 53: "lb_fl", 54: "m_fl", 55: "w_fl", 
            56: "rainbow_c"}

    def __init__(self,
                 device_ip: str,
                 device_type: Literal[0, 1, 2, 3, 4],
                 keep_alive: bool = True):
        """Initialize a device."""
        self.device_ip = device_ip
        self.device_type = device_type
        self.API_PORT = 5577

        self.last_connection = datetime.datetime.now()
        # current time is set as the latest connection

        self.keep_alive = keep_alive
        self.set_fresh_socket()

    def __repr__(self):
        # This representation needs to be this unusual 
        # to support lower python versions than 3.12

        keep_alive_status = "yes" if self.keep_alive else "no"
        return (f"MagicHomeDevice(IP: {self.device_ip}, "
                f"port: {self.API_PORT}, type: {self.device_type}, "
                f"keep alive: {keep_alive_status})")

    def set_fresh_socket(self):
        """Create a new socket, store it as self.socket and connect it.

        A socket object that has been used or closed cannot be reused,
        so a fresh one is built every time.
        """
        self.socket = None
        # Until the new socket is connected, there is no usable socket

        try:  # Try connecting
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = new_socket
            self.socket.settimeout(3)
            # The Socket will try to connect. If nothing happens after
            # 3 seconds (timeout), an Error will be raised.
            print("Trying to connect to device...\n")
            self.socket.connect((self.device_ip, self.API_PORT))
            print("Successfully connected to device.")

        except OSError as connection_e:  # Connection failed
            print("Socket-Error while trying to connect to the device. "
                  f"Details:\n{connection_e}")

            if self.socket is None:  # Never created, nothing to close
                socket_close_success = "not needed, no socket existed"

            else:
                print("Trying to close socket...")

                try:  # Try closing the socket after an error occured
                    self.socket.close()
                    self.socket = None
                    # Socket None equals a closed / unusable socket
                    print("Socket closed due to Socket-Error.")
                    socket_close_success = "successfully"

                except OSError as socket_close_e:  # Closing failed too
                    print("Socket-Error while trying to close socket. "
                          f"Details:\n{socket_close_e}")
                    socket_close_success = "unsuccessfully"

            # This error is raised so that no broken socket can be used
            # further, instead the user has to create a new correct one.
            # "from connection_e" keeps the original cause in the traceback.
            raise OSError("Socket closed "
                          f"{socket_close_success} after previous error.") from connection_e

    def turn_on(self):
        """Turn a device on."""
        if self.device_type < 4:
            self.send_bytes(0x71, 0x23, 0x0F, 0xA3)
        else:
            self.send_bytes(0xCC, 0x23, 0x33)

    def turn_off(self):
        """Turn a device off."""
        if self.device_type < 4:
            self.send_bytes(0x71, 0x24, 0x0F, 0xA4)
        else:
            self.send_bytes(0xCC, 0x24, 0x33)

    def get_status(self, return_debug_info: bool = False) -> dict:
        """Returns the current, human readable status of a device as a dictionary.

        If return_debug_info is set to True, 
        info like message head and model number will be included in the dictionary."""

        try:
            self.send_bytes(0x81, 0x8A, 0x8B, 0x96)
            status = self.socket.recv(14)

        except OSError as recv_e:
            raise OSError("Error while trying to fetch status from device.") from recv_e

        message_head = status[0]

        model_number = status[1]

        if status[2] == 0x23:
            on = True
        else: # 0x24
            on = False

        preset_name = None
        preset_number = None

        if status[3] in self.PRESETS_REV: # valid preset
            preset_name = self.PRESETS_REV[status[3]]
            preset_number = int(status[3])

        preset_slowdown = int(status[5])
        # For explanation, please refer to the docstring of send_preset()

        r, g, b = status[6], status[7], status[8]

        ww = status[9] # warm white

        version_number = status[10]

        cw = status[11] # cold white, stays at 0 for some device types

        checksum = status[13]

        if return_debug_info:
            status_dict = {"message_head": message_head, 
                           "model_number": model_number, "on": on, 
                           "preset_name": preset_name, 
                           "preset_number": preset_number, 
                           "preset_slowdown": preset_slowdown, 
                           "r": r, "g": g, "b": b, 
                           "ww": ww, "version_number": version_number, 
                           "cw": cw, "checksum": checksum}
        else:
            status_dict = {"on": on, "preset_name": preset_name, 
                           "preset_number": preset_number, 
                           "preset_slowdown": preset_slowdown, 
                           "r": r, "g": g, "b": b, 
                           "ww": ww, "cw": cw}
        return status_dict

        

    def change_color(self,
                      r: int = 0,
                      g: int = 0,
                      b: int = 0,
                      ww: int | None = None,
                      cw: int | None = None):
        """Update a device based upon what we're sending to it.

        RGB values are accepted as integers in the range of 0-255.
        White values are accepted as integers representing the range of
        0%-100%, and are allowed to have a value of None.
        However, please note that white and RGB values together raise a
        ValueError, just like two different types of white together.
        """
        # n = normalized
        n_r = self.norm_color(r)
        n_g = self.norm_color(g)
        n_b = self.norm_color(b)

        # Note: If whites were None, they are now converted into 0
        n_ww = self.norm_white(ww)
        n_cw = self.norm_white(cw)

        if (n_r != 0 or n_g != 0 or n_b != 0) and (n_ww != 0 or n_cw != 0):
            # Needs to raise an Exception, we do not want both at the same
            # time, because white gets ignored when passing white and RGB
            # values, which would otherwise confuse users.
            raise ValueError("Pass either RGB or white value, not both")

        if n_ww != 0 and n_cw != 0:
            raise ValueError(
                "Pass either cold white or warm white value, not both")

        if self.device_type in (0, 1):
            # Update RGB or RGB + WW device
            message = [0x31, n_r, n_g, n_b, n_ww, 0x00, 0x0f]
            self.send_bytes(*(message + [self.calculate_checksum(message)]))

        elif self.device_type == 2:
            # Update RGB + WW + CW device
            message = [0x31, n_r, n_g, n_b, n_ww, n_cw, 0x0f, 0x0f]
            self.send_bytes(*(message + [self.calculate_checksum(message)]))

        elif self.device_type == 3:
            # Update the white, or color, of a bulb.
            # mode sets the device to either ww (0x0f) or color (0xf0),
            # using the "magic numbers".
            mode = 0x0f if n_ww != 0 else 0xf0

            message = [0x31, n_r, n_g, n_b, n_ww, mode, 0x0f]
            self.send_bytes(*(message + [self.calculate_checksum(message)]))

        elif self.device_type == 4:
            # Update the white, or color, of a legacy bulb
            if n_ww != 0:  # ww mode
                message = [0x56, 0x00, 0x00, 0x00, n_ww, 0x0f, 0xaa,
                           0x56, 0x00, 0x00, 0x00, n_ww, 0x0f, 0xaa]
            else:  # color mode
                message = [0x56, n_r, n_g, n_b, 0x00, 0xf0, 0xaa]

            self.send_bytes(*(message + [self.calculate_checksum(message)]))

        else:
            # Device type other than [0,1,2,3,4] passed
            raise ValueError("Invalid Device Type")

    def norm_color(self, color_val: int):
        """Normalize a color value into the allowed 0-255 range."""
        if color_val < 0:
            return 0
        elif color_val > 255:
            return 255
        else:
            return color_val

    def norm_white(self, white_percent: int | None = None):
        """Normalize a white light value into the allowed 0%-100% range.

        White values are a percentage.
        """
        if (white_percent is None) or (white_percent < 0):
            return 0
        elif white_percent > 100:
            return 100
        else:
            return white_percent

    def send_preset(self, preset_name: str | None = None, preset_number: int | None = None, slowdown: int = 100):
        """Send a preset command to a device.

        The following abbreviations are used:

        r: red, g: green, b: blue, y: yellow, lb: light blue,
        m: magenta (pink), w: white, rainbow: rainbow (all colors).

        fade: fading, b: breathing, fl: flashing, c: change without
        transition. 
        
        If two colors are named together, connected with a +, they alternate.

        The slowdown value ranges from 1 to 31.
        
        Slowdown acts like a "brake" on the effect speed: a value of 31 
        means the brake is fully applied (slowest), while a value of 1 
        means the brake is not applied at all (fastest).

        Passing a preset number in the range of 0x25 (int 37)
        to 0x38 (int 56) instead of a preset name is possible, but
        passing both will raise a ValueError.

        The following presets are available:
        rainbow_fade, r_b, g_b, b_b, y_b, lb_b, m_b, w_b, r+g_b, r+b_b,
        g+b_b, rainbow_fl, r_fl, g_fl, b_fl, y_fl, lb_fl, m_fl, w_fl, rainbow_c
        """

        if slowdown not in range(1,32):
            raise ValueError("Slowdown ranges from 1 to 31.")
        # Raising a ValueError is better than clamping the value 
        # to prevent unexpected device behaviour.

        if preset_name is not None and preset_number is not None:
            raise ValueError("Pass either preset name or number, not both.")
        if preset_name is None and preset_number is None:
            raise ValueError("Pass either preset name or number.")
        
        if preset_number is None:
            if preset_name not in self.PRESETS:
                raise ValueError("The passed preset name is not available.")
            final_preset = self.PRESETS[preset_name]

        else:
            if preset_number not in range(37,57):
                # Raises Error instead of clamping to 
                # prevent unforseeable device behaviour.
                raise ValueError("The passed preset number is not available.")
            final_preset = preset_number

        # final_preset is the preset number that is calculated based on
        # the users input and sent to the device.
        if self.device_type == 4:
            self.send_bytes(0xBB, final_preset, slowdown, 0x44)
        else:
            message = [0x61, final_preset, slowdown, 0x0F]
            self.send_bytes(*(message + [self.calculate_checksum(message)]))

    def calculate_checksum(self, bytes_param):
        """Calculate the checksum from an array of bytes."""
        return sum(bytes_param) & 0xFF

    def send_bytes(self, *bytes_params):
        """Sends commands to the device."""
        try:
            self.reconnect()
            message_length = len(bytes_params)
            self.socket.send(struct.pack("B" * message_length, *bytes_params))
            self.last_connection = datetime.datetime.now()
        except OSError as socket_send_e:
            print("Socket-Error while trying to send entered bytes. "
                  f"Details:\n{socket_send_e}")
            raise  # the caller must know that nothing was sent

    def reconnect(self):
        """Reestablishes the connection.

        A connection that has not been used for 5 minutes is replaced,
        just like one that was closed because keep_alive is- set to False.
        """
        time_since_last_con = (datetime.datetime.now()
                               - self.last_connection).total_seconds()

        try:
            if not self.keep_alive:
                # Close the connection unless requested not to
                try:
                    self.socket.close()
                    self.socket = None
                    print("Socket closed due to keep_alive being False.")
                except OSError as socket_close_e:
                    print("Socket-Error while trying to close socket. "
                          f"Details:\n{socket_close_e}")

            if time_since_last_con >= 290 or self.socket is None:
                # 290s = roughly 5 minutes.
                # A used socket object cannot be reconnected, so a fresh
                # one is built. set_fresh_socket() also connects it.
                self.set_fresh_socket()

        except OSError as exc:
            if self.socket is not None:
                try:
                    self.socket.close()
                    self.socket = None
                    print("Socket closed due to Socket-Error. "
                          f"Details:\n{exc}")
                except OSError as socket_close_e:
                    print("Socket-Error while trying to close socket. "
                          f"Details:\n{socket_close_e}")
            else:
                print("Did not close socket, it was already closed "
                      "or inaccessible.")
            raise  # prevents usage of a broken socket
