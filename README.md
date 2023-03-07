# PantrySense (Raspberry Pi)
This is a part of my broader smart pantry project Rikōtodana. The project is currently in the prototype stage.

This repository includes software for the sensors (camera, reed switch & buttons) and output devices (buzzer and 3 LEDs and optionally a loudspeaker) that are directly connected to a Raspberry Pi.
All the measured data gets forwarded with an MQTT broker. The output devices also receive data through the MQTT broker. You need to set one up and change the credentials and broker address in `default_mqtt.json`.  
The addresses/numbers of the used pins for the respective components can be changed in `btn_cfg.json`, `buzz_cfg.json`, `led_cfg.json`, `cam_cfg.json` and `reed_cfg.json`.

The camera software assumes that you are only using one camera that is connected to the Raspberry Pi through the CSI interface.
The loudspeaker software plays its sounds on the system's standard pulseaudio audio output.

To run the software, you need to run the python scripts for the devices in the background (for example with the GNU tool `screen`).
Run `led_out.py` for the LED output, `buzzer.py` for the buzzer sound output, `buttons.py` for the button input, `camera.py` for the camera-based GTIN detection and `reed_sw.py` for the reed switch status.
### Security warning
Since this is still a prototype, many security measures are missing! Transport encryption for the MQTT messages has not been implemented yet.
