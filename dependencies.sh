#!/bin/bash

sudo apt-get update

wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm.zip

unzip ngrok-stable-linux-arm.zip

sudo mv ngrok /bin

pip install -r requirements.txt
