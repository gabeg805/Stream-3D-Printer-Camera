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

## Install any missing packages

Install the following package so that your **Picamera2** works:

```sudo apt install python3-picamera2```

As well as the following so that the code works:

```pip3 install numpy```

```pip3 install simplejpeg```

There could be more that you have to install, I'm not sure.  I was updating the
OS and firmware of my Raspberry Pi at the time, trying to get **Picamera 2** to
work, so there was a whirwind of stuff I was installing and updating.  If you
get any errors, reach out and I'll try to help you debug, and I'll update the
README.

## Setup camera in Prusa Connect

1. Open **Prusa Connect**.
2. Go to the **Camera** tab.
3. Click on **Add new other camera**.
4. Copy the **Token**.
5. In [stream_3dprinter_camera.py](stream_3dprinter_camera.py), look for the
   `PRINTER_TOKEN` variable and paste in the **Token** from step 4 there.

**Important:** If your copy of
[stream_3dprinter_camera.py](stream_3dprinter_camera.py) will be public, then
**DO NOT** do step 5.  Instead, do the following in place of step 5:

1. Create the file: `~/.api/prusa/token`
2. Paste the **Token** in this file. The script will read the **Token** from
   this file.

# Usage

## Start the stream

`python3 stream_3dprinter_camera.py`

This is a great way to test the _.py_ file to make sure you don't need to
install anything extra and it works the way you expect.

## View the stream

The video stream can be viewed at the following URL:

```http://IP_ADDRESS:PORT```

Where `IP_ADDRESS` is the IP address of your Raspberry Pi and `PORT` is the
port you want to use.  By default, `PORT = 8000`

Your URL will be something like `http://192.168.0.123:8000`

## Start the stream via systemd

Copy [stream-3dprinter-camera.service](stream-3dprinter-camera.service) into:

`~/.config/systemd/user/`

Start the _.service_ file:

`systemctl start --user stream-3dprinter-camera.service`

To automatically start the _.service_ file even if the Raspberry Pi is
restarted, then run:

`systemctl enable --user stream-3dprinter-camera.service`

## Frequently asked questions

### What do the global variables in [stream_3dprinter_camera.py](stream_3dprinter_camera.py) do?

#### PORT

The port that you'll have to use when viewing the stream.

Default: `8000`.

#### RESOLUTION

The resolution of the video/image. Using smaller resolutions seemed to crop out some of
the field of view of the camera, so take that into account if reducing this
value.

Default: `1920 x 1080`.

#### ROTATION

The number of degrees to rotate. Only 0 and 180 degrees are accepted.

Default: `180`.

#### BUFFER

The buffer count. A higher buffer count can mean that the camera will run more
smoothly and drop fewer frames, though the downside is that at higher
resolutions, there may not be enough memory available.

Default: `8`.

#### FPS

The number of frames per second to run the video at.

Default: `30`.

#### MOTION_THRESHOLD

The threshold above which it is determined that a motion event has occurred.
Pixel differences between the current and previous frame are measured in order
to compare against the threshold.

Default: `12`.

#### WAIT_AFTER_MOTION

Number of seconds to wait after a snapshot is saved and sent to **Prusa
Connect**.

Default: `30`.

#### WAIT_AFTER_N_LOOPS

Number of seconds to wait after some number of loops, defined by
**MOTION_N_LOOPS**, has occurred.

Default: `5`

#### MOTION_N_LOOPS

Number of loops to try and capture motion. Detecting motion is expensive so
only compare for this many number of loops and then wait for a bit so that
the Raspberry Pi does not have to do as much work as constantly trying to
detect motion.

Default: `15`.

#### PRINTER_SNAPSHOT_URL

The URL at which **Prusa Connect** expect snapshots to be sent to.

Default: `https://webcam.connect.prusa3d.com/c/snapshot`

#### PRINTER_TOKEN

The token of the 3D printer generated in **Prusa Connect**.  This should only
be hardcoded in the script if your copy **WILL NOT** be public.  If it will be
public, then you should save the token to a file and let the _.py_ script read
the file.

#### PRINTER_TOKEN_PATH

The path to the file that has the 3D printer token.  This is used so that the
printer token is not hardcoded in the event that your copy of the _.py_ script
is public.  If your copy is private, then this variable does not need to be
used.

Default: `~/.api/prusa/token`.

### Where do motion detection snapshots get saved?

Motion detection snapshots are saved with the following format:

```/tmp/motion_TIMESTAMP.jpg```

Where `TIMESTAMP` is the date and time at which the snapshot was taken in the
format **YYYY-MM-DD_hhmmss**.

