import json
import os

import numpy as np

# if not os.environ.get('PYOPENGL_PLATFORM'):
#     os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

# import OpenGL
# OpenGL.USE_ACCELERATE = False

from OpenGL import arrays
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.osmesa import *

from PIL import Image

from cmlibs.zinc.context import Context
from cmlibs.zinc.sceneviewer import Sceneviewer


def write_image(buffer, filename):
    image = np.frombuffer(buffer, dtype=np.uint8).reshape(
        (OSMesaGetIntegerv(OSMESA_HEIGHT), OSMesaGetIntegerv(OSMESA_WIDTH), 4))

    # Flip vertically and save as PNG
    image = np.flipud(image)
    Image.fromarray(image, 'RGBA').convert("RGB").save(filename)


def write_ppm(buf, filename):
    f = open(filename, "w")
    if f:
        h, w, c = buf.shape
        print("P3", file=f)
        print("# ascii ppm file created by osmesa", file=f)
        print("%i %i" % (w, h), file=f)
        print("255", file=f)
        for y in range(h - 1, -1, -1):
            for x in range(w):
                pixel = buf[y, x]
                l = " %3d %3d %3d" % (pixel[0], pixel[1], pixel[2])
                f.write(l)
            f.write("\n")


def init_ctx(width, height):
    ctx = OSMesaCreateContext(OSMESA_RGBA, None)
    # ctx = OSMesaCreateContextExt(OSMESA_RGBA, 32, 0, 0, None)
    buf = arrays.GLubyteArray.zeros((height, width, 4))
    assert (OSMesaMakeCurrent(ctx, buf, GL_UNSIGNED_BYTE, width, height))
    assert (OSMesaGetCurrentContext())

    z = glGetIntegerv(GL_DEPTH_BITS)
    s = glGetIntegerv(GL_STENCIL_BITS)
    a = glGetIntegerv(GL_ACCUM_RED_BITS)
    print("Depth=%d Stencil=%d Accum=%d" % (z, s, a))

    print("Width=%d Height=%d" % (OSMesaGetIntegerv(OSMESA_WIDTH),
                                  OSMesaGetIntegerv(OSMESA_HEIGHT)))
    return ctx, buf


def free_ctx(ctx, buf):
    write_ppm(buf, 'osmesa_output.ppm')
    write_image(buf, 'osmesa_output.jpeg')
    OSMesaDestroyContext(ctx)


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
    # buffer = arrays.GLubyteArray.zeros((height, width, 4))
    buffer = (ctypes.c_ubyte * (width * height * 4))()

    # Make the context current
    result = osmesa.OSMesaMakeCurrent(ctx, buffer, GL_UNSIGNED_BYTE, width, height)
    if not result:
        raise RuntimeError("OSMesaMakeCurrent failed")

    assert (osmesa.OSMesaGetCurrentContext())

    print("Width=%d Height=%d" % (osmesa.OSMesaGetIntegerv(OSMESA_WIDTH),
                                  osmesa.OSMesaGetIntegerv(OSMESA_HEIGHT)))
    # Set up the OpenGL viewport and clear color
    glClearColor(0, 0, 255, 0)
    # glMatrixMode(GL_MODELVIEW)
    # glLoadIdentity()

    # _do_opengl_drawing(height, width)
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
    glFinish()


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
    here = os.path.dirname(os.path.abspath(__file__))
    print("Current directory:", here)
    print("Zinc drawing with height:", height, "width:", width)
    c = Context('pic')
    print("Zinc context created:", c.isValid())
    material_module = c.getMaterialmodule()
    print("Zinc material module:", material_module.isValid())
    material_module.defineStandardMaterials()
    print("Defined standard materials in Zinc material module.")
    r = c.getDefaultRegion()
    print("Zinc default region:", r.isValid())
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
    scene_viewer = c.getSceneviewermodule()
    sceneviewer = scene_viewer.createSceneviewer(Sceneviewer.BUFFERING_MODE_DOUBLE,
                                                 Sceneviewer.STEREO_MODE_DEFAULT)
    sceneviewer.setViewportSize(width, height)
    # sceneviewer.readDescription(json.dumps(scene_description))
    # Workaround for order independent transparency producing a white output
    # and in any case, sceneviewer transparency layers were not being serialised by Zinc.
    sceneviewer.setTransparencyMode(Sceneviewer.TRANSPARENCY_MODE_SLOW)
    sv = {
        "AntialiasSampling": 0,
        "BackgroundColourRGB": [
            0.2,
            0.4,
            0.6
        ],
        "EyePosition": [
            -3.6098355377165454,
            1.37148168884913,
            3.358935996438843
        ],
        "FarClippingPlane": 9.118039239824375,
        "LightingLocalViewer": False,
        "LightingTwoSided": True,
        "LookatPosition": [
            0.0,
            0.0,
            0.0
        ],
        "NearClippingPlane": 1.4267954023631337,
        "PerturbLinesFlag": False,
        "ProjectionMode": "PERSPECTIVE",
        "Scene": None,
        "Scenefilter": "default",
        "TranslationRate": 1,
        "TransparencyLayers": 1,
        "TransparencyMode": "FAST",
        "TumbleRate": 1.5,
        "UpVector": [
            0.2542897680821075,
            0.9598259398927999,
            -0.11862073578279417
        ],
        "ViewAngle": 0.6981317007977244,
        "ZoomRate": 1
    }
    s = r.getScene()
    print("Zinc scene:", s.isValid())
    sceneviewer.setScene(s)
    res = s.readDescription(json.dumps(t), True)
    print("Read description result:", res)
    res = sceneviewer.readDescription(json.dumps(sv))
    print("Sceneviewer read description result:", res)
    set_true_for_segfault = True
    print(os.path.join(here, 'sphere.exf'), os.path.isfile(os.path.join(here, 'sphere.exf')), os.path.getsize(os.path.join(here, 'sphere.exf')))
    res = r.readFile(os.path.join(here, 'sphere.exf')) if set_true_for_segfault else 0
    print("Read file result:", res)
    res = s.readDescription(json.dumps(t), True)
    print("Read description result:", res)
    # res = sceneviewer.readDescription(json.dumps(sv))
    # print("Sceneviewer read description result:", res)
    sceneviewer.writeImageToFile('osmesa_output.jpeg', False, width, height, 4, 0)
    return r


if __name__ == "__main__":
    # main()
    print("Starting offscreen rendering with OSMesa...")
    ctx, buf = init_ctx(3260, 2048)
    print("Initialized OSMesa context and buffer.")
    _do_zinc_drawing(2048, 3260)
    print("Zinc drawing completed.")
    free_ctx(ctx, buf)
    print("Freed OSMesa context and buffer.")
    # draw_zinc_picture_offscreen_mesa()
    # draw_zinc_picture_offscreen_pyside6()
    print("Rendered image saved as osmesa_output.jpeg")
