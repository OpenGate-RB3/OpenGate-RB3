## ON HOST PC

sudo pacman -S mosquitto

sudo mkdir /etc/mosquitto/conf.d/

sudo vim /etc/mosquitto/conf.d/externalListen.conf

put this into there:

listener 1883 0.0.0.0
allow_anonymous true

sudo vim /etc/mosquitto/mosquitto.conf

include_dir /etc/mosquitto/conf.d

## ON DEVICE

cd /opt/openGateExtensions/
wget https://github.com/OpenGate-RB3/Open-Gate-MQTT-Client/releases/download/1.0.0/openGateMqttPython.cpython-312-aarch64-linux-gnu.so
