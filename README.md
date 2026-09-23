# Easy Magic Home
Easy to use API to control devices normally using the proprietary Magic Home smartphone app.

## Supported device types
- RGB Controllers (Type 0)
- RGB+WW Controllers (Type 1)
- RGB+WW+CW Controllers (Type 2)
- Bulbs using Firmware v.4 and greater (Type 3)
- Legacy Bulbs using Firmware v.3 and lower (Type 4)

## Abbreviations used
- RGB: Red, Green, Blue
- WW: Warm White
- CW: Cold White

## Methods
Define a new Magic Home device
> Enter the correct IP of the device in device_ip.  
> This is the most common source of error. 
I suggest setting the device to a fixed IP-address in your network, and verifying that the address is correct.  
> Enter the device type (see above) in device_type  
> if keep_alive is set to False, the socket will automatically reconnect before every attempt to communicate with the device.  
> Otherwise (default), it will only reconnect when trying to communicate again after 5 minutes of inactivity.
```python
MagicHomeDevice(device_ip: str, device_type: Literal[0, 1, 2, 3, 4], keep_alive: bool)
```

Create, save and connect new socket  
`set_fresh_socket()`

Turn device on  
`turn_on()`

Turn device off  
`turn_off()`

Get device status  
> Setting return_debug_info to True will return message head and model number.  
Only byte 4 and 12 from the raw byte packet are not included, 
since information online and test results return contradicting information on what these bytes represent.  
```python
get_status(return_debug_info: bool)
```

Change device color
> Please note: Pass only color, or warm white, or cold white, 
combining types will raise a ValueError.   
```python
change_color(r: int, g: int, b: int, ww: int, cw: int)
```

Normalize RGB color values into the allowed 0-255 range  
`norm_color(color_val: int)`

Normalize white light values into the allowed 0-100% range  
`norm_white(white_percent: int)`

Select one of the device lighting presets  
> e.g. a colorful fade or blue breathing  

> The slowdown parameter acts like a "brake" on the effect speed: a value of 31 
means the brake is fully applied (slowest), while a value of 1 
means the brake is not applied at all (fastest).

> Passing a preset number, which stems from the raw device code,
in the range of 0x25 (int 37) to 0x38 (int 56) instead of a preset name is also possible, 
but please note that passing both will raise a ValueError.

>The following presets are available:

| Color(s) | fade (fading) | b (breathing) | fl (flashing) | c (change without transition) |
| :--- | :--- | :--- | :--- | :--- |
| **rainbow** | rainbow_fade / 37 | | rainbow_fl / 48 | rainbow_c / 56 |
| **r** (red) | | r_b / 38 | r_fl / 49 | |
| **g** (green) | | g_b / 39 | g_fl / 50 | |
| **b** (blue) | | b_b / 40 | b_fl / 51 | |
| **y** (yellow) | | y_b / 41 | y_fl / 52 | |
| **lb** (light blue) | | lb_b / 42 | lb_fl / 53 | |
| **m** (magenta) | | m_b / 43 | m_fl / 54 | |
| **w** (white) | | w_b / 44 | w_fl / 55 | |
| **r+g** (red and green) | | r+g_b / 45 | | |
| **r+b** (red and blue) | | r+b_b / 46 | | |
| **g+b** (green and blue) | | g+b_b / 47 | | |

```python
send_preset(preset_name: str, preset_number: int, slowdown: int)
```

Calculate the checksum from an array of bytes  
> This utility method is needed because the device expects a single byte checksum at the end of the byte array sent to it.
```python
calculate_checksum(bytes_param)
```

Send commands to the device as raw bytes  
> The advantage of sending raw bytes is that it's very efficient runtime-wise and reduces overhead.  
> This utility method is used by almost all other methods, for example to change color or to select a preset.
```python
send_bytes(*bytes_params)
```

Reconnect to the defined socket  
> Reestablishes the connection to the device  
> Usually called automatically by other methods if the device either hasn't been connected to in 5 minutes or if keep_alive is set to False.  
```python
reconnect()
```

## In-depth usage examples for the most important methods
> Define a new device  
```python
light_bulb = MagicHomeDevice(
    device_ip="192.169.176.12", 
    device_type=1, 
    keep_alive=True
    )
```
> Turn on the device  
> It will use the last color it has been set to. 
```python
light_bulb.turn_on()
```

> Change the device's color to pink
```python
light_bulb.change_color(255, 0, 255)
```

> Set the device to bright, warm white
```python
light_bulb.change_color(ww=100)
```

> Return current light status including debug info
```python
light_bulb.get_status(return_debug_info=True)
```

> Make the device breathe slowly in alternating red and blue colors
```python
light_bulb.send_preset(preset_name=r+b_b, slowdown=10)
```

> Make the device flash quickly in green using a preset number
```python
send_preset(preset_number=50, slowdown=1)
```

> Turn off the device
```python
light_bulb.turn_off()
```



## Miscellaneous
Note on error handling:
turn_on(), turn_off(), change_color() and send_preset()
propagate OSError to the caller. Use try/except when using this module.

Original version:
Copyright 2016, Adam Kempenich. Licensed under MIT.
https://github.com/adamkempenich
