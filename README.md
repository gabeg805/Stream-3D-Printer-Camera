# Stream your 3D printer camera

Here's the most straightforward way I can think of to stream video from the
camera pointed at your 3D printer and, if motion is detected, send a snapshot
to **Prusa Connect**.

The video stream can be watched at the following URL:

```http://**IP_ADDRESS**:**PORT**```

Motion detection snapshots are saved with the following format:

```/tmp/motion_**TIMESTAMP**.jpg```

All this code I got from examples online, which are linked in the python source
code if you want to reference anything I used.

# Don't Panic

You don't need to have some arcane knowledge of setting up servers and opening
up ports and whatnot.  The code will do this for you.

# Getting started

## Install

You'll have to install the following package:

```sudo apt install python3-picamera2```

As well as the following with **pip3**:

```pip3 install numpy```
```pip3 install simplejpeg```

There could be more that you have to install, I'm not sure.  I was updating the
OS and firmware of my Raspberry Pi at the time, trying to get **Picamera 2** to
work, so there was a whirwind of stuff I was installing and updating.  If you
get any errors, reach out and I'll try to help you debug, and I can also update
the README.


