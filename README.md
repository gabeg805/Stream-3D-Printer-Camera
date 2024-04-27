# Stream your 3D printer camera

Here's the most straightforward way I can think of to stream video from the
camera pointed at your 3D printer and, if motion is detected, send a snapshot
to **Prusa Connect**.

A lot of this code I got from examples online, which are linked in 
[stream_3dprinter_camera.py](stream_3dprinter_camera.py) if you want to
reference anything I used.

# Don't Panic

You don't need to have some arcane knowledge of setting up servers and opening
up ports and whatnot.  The code will do this for you.

All you'll have to do is do a little bit in **Prusa Connect** and then just
change one variable in a python file.

# Prerequisites

## Install

You'll have to install the following package:

```sudo apt install python3-picamera2```

As well as the following with **pip3**:

```pip3 install numpy```

```pip3 install simplejpeg```

There could be more that you have to install, I'm not sure.  I was updating the
OS and firmware of my Raspberry Pi at the time, trying to get **Picamera 2** to
work, so there was a whirwind of stuff I was installing and updating.  If you
get any errors, reach out and I'll try to help you debug, and I'll update the
README.

## Setup camera in Prusa Connect

You'll have to setup a camera in **Prusa Connect** before you can use the code.

1. Open **Prusa Connect**.
2. Go to the **Camera** tab.
3. Click on **Add new other camera**.
4. Copy the **Token**.
5. In [stream_3dprinter_camera.py](stream_3dprinter_camera.py), look for the
   `PRINTER_TOKEN` variable and paste in the **Token** from step 4 there.

If you're saving your copy of this repo online, then **DO NOT** do step 5.
Instead, do the following in place of step 5:

1. Create the file: `~/.api/prusa/token`
2. Paste the **Token** in this file. The script will read the **Token** from
   this file.

# Usage

## Start the stream

To start the stream, run

`python3 stream_3dprinter_camera.py`

This is a great way to test
[stream_3dprinter_camera.py](stream_3dprinter_camera.py) to make sure you don't
need to install anything extra and it works the way you expect.

## View the stream

The video stream can be watched at the following URL:

```http://IP_ADDRESS:PORT```

Where `IP_ADDRESS` is the IP address of your Raspberry Pi and `PORT` is the
port you want to use.

The URL will be something like `http://192.168.0.123:8000`

## Start the stream via systemd

Copy [stream-3dprinter-camera.service](stream-3dprinter-camera.service) into:

`~/.config/systemd/user/`

Start the _.service_ file:

`systemctl start --user stream-3dprinter-camera.service`

To have the camera stream even if the Raspberry Pi is restarted, then run:

`systemctl enable --user stream-3dprinter-camera.service`

## Frequently asked questions

### Where do motion detection snapshots get saved?

Motion detection snapshots are saved with the following format:

```/tmp/motion_TIMESTAMP.jpg```

Where `TIMESTAMP` is the date and time at which the snapshot was taken in the
format **YYYY-MM-DD_hhmmss**.

