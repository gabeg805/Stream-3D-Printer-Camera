#!/usr/bin/python3
# 
# NAME
#     stream_3dprinter_camera.py
# 
# SYNOPSIS
#     python3 stream_3dprinter_camera.py
# 
# DESCRIPTION
#     Stream video from the camera and if motion is detected, send a snapshot
#     to Prusa Connect.
#     
#     The video stream can be watched at the following URL:
#     
#         http://<IP_ADDRESS>:<PORT>
#     
#     Motion detection snapshots are saved with the following format:
#     
#         <SNAPSHOT_DIR>/motion_<TIMESTAMP>.jpg
#     
# PREREQUISITES
#     Install the following packages:
#     
#         * python3-picamera2
#               - Do not install this with pip. See documentation as to why
#         * numpy
#         * simplejpeg
#     
#     In Prusa Connect:
#     
#         1. Add a "new other camera"
#     
#         2. Copy the "Token"
#     
#         3. Replace the "PRINTER_TOKEN" variable with the "Token" from #2.
#            If uploading your code to Github, DO NOT hardcode the "Token"
#            in the script.  Do the following instead:
#     
#                a. Read the comment above the "PRINTER_TOKEN" and
#                   "PRINTER_TOKEN_PATH" variables.
#                b. Save the value of the "Token" to a file which
#                   "PRINTER_TOKEN_PATH" points to.
#                c. The script will reads the "PRINTER_TOKEN_PATH" file and
#                   populate "PRINTER_TOKEN" with it.
# 
# NOTES
#     The following examples from the Picamera2 Library documentation were
#     used as a reference.
#     
#         How to rotate the video by 180 deg:
#         
#             * https://github.com/raspberrypi/picamera2/blob/main/examples/rotation.py
#         
#         How to capture motion:
#         
#             * https://github.com/raspberrypi/picamera2/blob/main/examples/capture_motion.py
#         
#         How to take a still image while streaming video:
#         
#             * https://github.com/raspberrypi/picamera2/blob/main/examples/still_during_video.py
#         
#         How to setup a server to stream video:
#         
#             * https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py
#     
#     See the Picamera2 Library documentation for more information:
#     
#         https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
# 

import argparse
import io
import logging
import numpy
import os
import socketserver
import sys
import time
from datetime import datetime
from http import server
from threading import Condition, Thread

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from libcamera import controls, Transform

# Stream port
PORT = 8000

# Video/image resolution. Using smaller resolutions seemed to crop out some of
# the field of view of the camera, so take that into account if reducing this
# value
RESOLUTION = (1920, 1080)

# Number of degrees to rotate. Only 0 and 180 degrees are accepted
ROTATION = 0

# Buffer count. A higher buffer count can mean that the camera will run more
# smoothly and drop fewer frames, though the downside is that at higher
# resolutions, there may not be enough memory available
BUFFER = 8

# Frame rate per second
FPS = 30

# Motion threshold. Pixel differences between the current and previous frame
# are measured. If this threshold is exceeded, then it is treated as a motion
# event
MOTION_THRESHOLD = 12

# Number of seconds to wait after a snapshot was saved and sent to Prusa
# Connect
WAIT_AFTER_MOTION = 30

# Number of seconds to wait after some number of loops, defined by
# MOTION_N_LOOPS, has occurred
WAIT_AFTER_N_LOOPS = 5

# Number of loops to try and capture motion. Detecting motion is expensive so
# only compare for this many number of loops and then wait for a bit so that
# the Raspberry Pi does not have to do as much work as constantly trying to
# detect motion.
MOTION_N_LOOPS = 15

# Directory where motion detection snapshots are saved
SNAPSHOT_DIR = "/tmp"

# Printer snapshot URL
PRINTER_SNAPSHOT_URL = "https://webcam.connect.prusa3d.com/c/snapshot"

# Printer token. This is generated in Prusa Connect and I just saved the string
# to a file so that it was not hardcoded in this script
PRINTER_TOKEN = ""

# Path to the printer token. This is just used to read the token, but if you
# want to hardcode it below, that works too
PRINTER_TOKEN_PATH = os.path.join(os.environ["HOME"], ".api", "prusa", "token")

# Check if the path to the printer token exists
if os.path.isfile(PRINTER_TOKEN_PATH):

	# Read the token from the file
	with open(PRINTER_TOKEN_PATH, "r") as handle:
		PRINTER_TOKEN = handle.readline().strip()

# Camera fingerprint for the printer. This is just a random string I generated
PRINTER_CAMERA_FINGERPRINT = "d730a87e9ba94ff3b7960d89698eaeed"

class StreamingOutput(io.BufferedIOBase):

	def __init__(self):
		self.frame = None
		self.condition = Condition()

	def write(self, buf):
		with self.condition:
			self.frame = buf
			self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):

	def do_GET(self):
		"""
		This method has been overridden so that it always shows the stream. It will
		not show a 404 error page or anything.

		If you want to add that logic in and check for specific paths such as in the
		"How to setup a server to stream video" from the NOTES section in the
		header of this script, you can also go that route.
		"""

		self.send_response(200)
		self.send_header('Age', 0)
		self.send_header('Cache-Control', 'no-cache, private')
		self.send_header('Pragma', 'no-cache')
		self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
		self.end_headers()

		try:
			while True:
				with output.condition:
					output.condition.wait()
					frame = output.frame

				self.wfile.write(b'--FRAME\r\n')
				self.send_header('Content-Type', 'image/jpeg')
				self.send_header('Content-Length', len(frame))
				self.end_headers()
				self.wfile.write(frame)
				self.wfile.write(b'\r\n')

		except Exception as e:
			logging.warning(
				'Removed streaming client %s: %s',
				self.client_address, str(e))

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True

def detect_motion(picam2):
	"""
	Detect any motion in front of the camera and take a pic if motion is detected.
	"""

	prev = None
	w, h = RESOLUTION
	nloop = 0

	# Check if the printer token is not set
	if not PRINTER_TOKEN:

		# Do not attempt to detect motion if there is no token
		print("ERROR: Unable to detect motion because the PRINTER_TOKEN is not set.")
		return

	# Wait to detect motion
	while True:

		# Look at the current buffered frame
		cur = picam2.capture_buffer("main")
		cur = cur[:w * h].reshape(h, w)

		# Make sure there is a previous image to compare against
		if prev is not None:

			# Measure pixels differences between current and
			# previous frame
			mse = numpy.square(numpy.subtract(cur, prev)).mean()
			#print(f"Testing motion threshold : {mse}")

			# Check if enough differences were measured to indicate a motion event
			if mse > MOTION_THRESHOLD:

				# Get the current time
				now = datetime.now()
				timestamp = now.strftime("%Y-%m-%d_%H%M%S")

				# Take a picture of the motion
				filepath = f"{SNAPSHOT_DIR}/motion_{timestamp}.jpg"
				request = picam2.capture_request()
				#print(f"Motion detected : {mse} | File : {filepath}")

				request.save("main", filepath)
				request.release()

				# Send the picture to the printer
				cmd = f'curl -X PUT "{PRINTER_SNAPSHOT_URL}" -H "accept: */*" -H "content-type: image/jpg" -H "fingerprint: {PRINTER_CAMERA_FINGERPRINT}" -H "token: {PRINTER_TOKEN}" --data-binary "@{filepath}" --no-progress-meter --compressed'
				os.system(cmd)

				# Delay until potentially taking another picture
				time.sleep(WAIT_AFTER_MOTION)

				# Reset the current frame and loop counter
				cur = None
				nloop = 0

		# Set the previous image
		prev = cur

		# Check if number of loops is set
		if MOTION_N_LOOPS > 0:

			# Check if should wait before proceeding
			nloop = (nloop+1) % MOTION_N_LOOPS

			if nloop == 0:
				time.sleep(WAIT_AFTER_N_LOOPS)
	return

def start_stream(picam2):
	"""
	Start streaming the camera to a server.
	"""

	try:
		# Stream the camera video in the server
		httpd = StreamingServer(("", PORT), StreamingHandler)
		httpd.serve_forever()

	except KeyboardInterrupt:
		pass

	finally:
		# Stop streaming
		picam2.stop_recording()
	return

# Create the argument parser
parser = argparse.ArgumentParser(
	prog=os.path.basename(sys.argv[0]),
	description="Stream video from the camera and if motion is detected, send a snapshot to Pruse Connect.")

# Add arguments to the parser
res = f"{RESOLUTION[0]}x{RESOLUTION[1]}"

parser.add_argument("-f", "--fps",
	default=FPS,
	type=int,
	help=f"Frames per second to run the camera at. Default: {FPS}")

parser.add_argument("-p", "--port",
	default=PORT,
	type=int,
	help=f"Port to stream the camera video at. Default: {PORT}")

parser.add_argument("-r", "--rot",
	default=ROTATION,
	type=int,
	help=f"Number of degrees to rotate the camera video. Valid: 0, 180. Default: {ROTATION}")

parser.add_argument("-s", "--size",
	default=res,
	help=f"Resolution of the camera video. Default: {res}")

parser.add_argument("-N", "--no-detect",
	action="store_true",
	default=False,
	help=f"Do not detect motion and send pics to Prusa Connect.")

# Parse the arguments
args = parser.parse_args()

# Set the defaults
FPS        = args.fps
PORT       = args.port
ROTATION   = args.rot
RESOLUTION = tuple(int(i) for i in args.size.split("x"))

# Setup how snapshots will be saved
output = StreamingOutput()

# Setup transform to rotate the video/image of the camera
transform = Transform(hflip=1, vflip=1) if ROTATION == 180 else Transform()

# Initialize the camera
picam2 = Picamera2()

# Configure the camera
config = picam2.create_video_configuration( \
	buffer_count=BUFFER,
	main={"size": RESOLUTION},
	transform=transform)

picam2.configure(config)

# Set auto focus and frame rate of the camera
picam2.set_controls({ \
	"AfMode": controls.AfModeEnum.Auto,
	"AfSpeed": controls.AfSpeedEnum.Normal,
	"FrameRate": FPS})

# Start the camera
picam2.start_recording(JpegEncoder(), FileOutput(output))

# Check if should detect motion
if not args.no_detect:

	# Create thread to detect motion
	thread = Thread(target=detect_motion, args=[picam2], daemon=True)
	thread.start()

# Start the stream
start_stream(picam2)

