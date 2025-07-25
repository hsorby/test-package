import ctypes
import numpy as np
from OpenGL.GL import *
from PIL import Image

# Load the OSMesa library
osmesa = ctypes.CDLL("libOSMesa.so")

# Define constants
OSMESA_RGBA = 0x1908
GL_UNSIGNED_BYTE = 0x1401

# Define function prototypes
osmesa.OSMesaCreateContext.argtypes = [ctypes.c_uint, ctypes.c_void_p]
osmesa.OSMesaCreateContext.restype = ctypes.c_void_p

osmesa.OSMesaMakeCurrent.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_int]
osmesa.OSMesaMakeCurrent.restype = ctypes.c_int

osmesa.OSMesaDestroyContext.argtypes = [ctypes.c_void_p]
osmesa.OSMesaDestroyContext.restype = None

# Create an OSMesa context
ctx = osmesa.OSMesaCreateContext(OSMESA_RGBA, None)

# Define the size of the offscreen buffer
width, height = 256, 256
buffer = (ctypes.c_ubyte * (width * height * 4))()

# Make the context current
result = osmesa.OSMesaMakeCurrent(ctx, buffer, GL_UNSIGNED_BYTE, width, height)
if not result:
    raise RuntimeError("OSMesaMakeCurrent failed")

# Set up the OpenGL viewport and clear color
glViewport(0, 0, width, height)
glClearColor(0.2, 0.4, 0.6, 1.0)
glClear(GL_COLOR_BUFFER_BIT)

# Draw a simple triangle
glBegin(GL_TRIANGLES)
glColor3f(1.0, 0.0, 0.0)
glVertex2f(-0.6, -0.4)
glColor3f(0.0, 1.0, 0.0)
glVertex2f(0.6, -0.4)
glColor3f(0.0, 0.0, 1.0)
glVertex2f(0.0, 0.6)
glEnd()
glFlush()

# Convert the buffer to a NumPy array and reshape
image = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 4))

# Flip vertically and save as PNG
image = np.flipud(image)
Image.fromarray(image, 'RGBA').save("osmesa_output.png")

# Clean up
osmesa.OSMesaDestroyContext(ctx)

print("Rendered image saved as osmesa_output.png")
