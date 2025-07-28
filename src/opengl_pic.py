import ctypes
import json

import numpy as np
import OpenGL
from OpenGL import arrays
from OpenGL.raw.osmesa.mesa import OSMESA_WIDTH, OSMESA_HEIGHT

OpenGL.USE_ACCELERATE = False

from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
from cmlibs.zinc.context import Context
from cmlibs.zinc.sceneviewer import Sceneviewer


def draw_zinc_picture_offscreen_mesa():
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

    width, height = 3260, 2048
    buffer = arrays.GLubyteArray.zeros((height, width, 4))
    # buffer = (ctypes.c_ubyte * (width * height * 4))()

    # Make the context current
    result = osmesa.OSMesaMakeCurrent(ctx, buffer, GL_UNSIGNED_BYTE, width, height)
    if not result:
        raise RuntimeError("OSMesaMakeCurrent failed")

    assert(osmesa.OSMesaGetCurrentContext())

    print("Width=%d Height=%d" % (osmesa.OSMesaGetIntegerv(OSMESA_WIDTH),
                                  osmesa.OSMesaGetIntegerv(OSMESA_HEIGHT)))
    # Set up the OpenGL viewport and clear color
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    _do_opengl_drawing(height, width)
    # r = _do_zinc_drawing(height, width)
    image = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 4))

    # Flip vertically and save as PNG
    image = np.flipud(image)
    Image.fromarray(image, 'RGBA').convert("RGB").save("osmesa_output.jpeg")
    # print(r)

    glFinish()
    # Clean up
    osmesa.OSMesaDestroyContext(ctx)


def _do_opengl_drawing(height, width):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glClearColor(0.2, 0.4, 0.6, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    # gluPerspective(45.0, width / float(height), 0.1, 100.0)
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


def draw_zinc_picture_offscreen_pyside6():
    from PySide6 import QtGui

    if QtGui.QGuiApplication.instance() is None:
        QtGui.QGuiApplication([])

    off_screen = QtGui.QOffscreenSurface()
    off_screen.create()
    if off_screen.isValid():
        context = QtGui.QOpenGLContext()
        if context.create():
            context.makeCurrent(off_screen)

            # r = _do_zinc_drawing(2048, 3260)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, 1, 0)

            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            if status != GL_FRAMEBUFFER_COMPLETE:
                print("Framebuffer is not complete:", status)

            _do_opengl_drawing(2048, 3260)


def _do_zinc_drawing(height, width):
    c = Context('pic')
    material_module = c.getMaterialmodule()
    material_module.defineStandardMaterials()
    r = c.getDefaultRegion()
    r.readFile('sphere.exf')
    s = r.getScene()
    t = {
        "Graphics": [
            {
                "BoundaryMode": "ALL",
                "CoordinateField": "coordinates",
                "ElementFaceType": "ALL",
                "FieldDomainType": "MESH2D",
                "Material": "orange",
                "RenderLineWidth": 1,
                "RenderPointSize": 1,
                "RenderPolygonMode": "SHADED",
                "Scenecoordinatesystem": "LOCAL",
                "SelectMode": "ON",
                "SelectedMaterial": "default_selected",
                "Surfaces": {},
                "Tessellation": "default",
                "Type": "SURFACES",
                "VisibilityFlag": True
            }
        ],
        "VisibilityFlag": True
    }
    r = s.readDescription(json.dumps(t), True)
    scene_viewer = c.getSceneviewermodule()
    sceneviewer = scene_viewer.createSceneviewer(Sceneviewer.BUFFERING_MODE_DOUBLE,
                                                 Sceneviewer.STEREO_MODE_DEFAULT)
    sceneviewer.setViewportSize(width, height)
    # sceneviewer.readDescription(json.dumps(scene_description))
    # Workaround for order independent transparency producing a white output
    # and in any case, sceneviewer transparency layers were not being serialised by Zinc.
    sceneviewer.setTransparencyMode(Sceneviewer.TRANSPARENCY_MODE_SLOW)
    sceneviewer.setScene(s)
    sv = {
        "AntialiasSampling": 0,
        "BackgroundColourRGB": [
            1.0,
            1.0,
            1.0
        ],
        "EyePosition": [
            -2.740519738838613,
            1.0412032904203423,
            2.5500414917958008
        ],
        "FarClippingPlane": 7.88551982890656,
        "LightingLocalViewer": False,
        "LightingTwoSided": True,
        "LookatPosition": [
            0.0,
            0.0,
            0.0
        ],
        "NearClippingPlane": 0.1942759914453282,
        "PerturbLinesFlag": False,
        "ProjectionMode": "PERSPECTIVE",
        "Scene": None,
        "Scenefilter": "default",
        "TranslationRate": 1,
        "TransparencyLayers": 1,
        "TransparencyMode": "FAST",
        "TumbleRate": 1.5,
        "UpVector": [
            0.2542897680821095,
            0.9598259398928073,
            -0.11862073578279508
        ],
        "ViewAngle": 0.6981317007977255,
        "ZoomRate": 1
    }
    sceneviewer.readDescription(json.dumps(sv))
    sceneviewer.writeImageToFile('osmesa_output.jpeg', False, width, height, 4, 0)
    return r


def main():
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


if __name__ == "__main__":
    # main()
    draw_zinc_picture_offscreen_mesa()
    # draw_zinc_picture_offscreen_pyside6()
    print("Rendered image saved as osmesa_output.png")
