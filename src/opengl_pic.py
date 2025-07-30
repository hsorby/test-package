import json
import os

import numpy as np

# if not os.environ.get('PYOPENGL_PLATFORM'):
#     os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

# import OpenGL
# OpenGL.USE_ACCELERATE = False

from OpenGL import GL
from OpenGL import arrays
from OpenGL.osmesa import (
    OSMesaCreateContextAttribs, OSMesaMakeCurrent, OSMesaGetCurrentContext,
    OSMESA_FORMAT, OSMESA_RGBA, OSMESA_PROFILE, OSMESA_COMPAT_PROFILE,
    OSMESA_CONTEXT_MAJOR_VERSION, OSMESA_CONTEXT_MINOR_VERSION,
    OSMESA_HEIGHT, OSMESA_WIDTH,
    OSMESA_DEPTH_BITS, OSMesaGetIntegerv, OSMesaDestroyContext
)

from PIL import Image

from cmlibs.zinc.context import Context
from cmlibs.zinc.sceneviewer import Sceneviewer


def write_image(buf, filename):
    image = np.frombuffer(buf, dtype=np.uint8).reshape(
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
    attrs = arrays.GLintArray.asArray([
        OSMESA_FORMAT, OSMESA_RGBA,
        OSMESA_DEPTH_BITS, 24,
        OSMESA_PROFILE, OSMESA_COMPAT_PROFILE,
        OSMESA_CONTEXT_MAJOR_VERSION, 2,
        OSMESA_CONTEXT_MINOR_VERSION, 1,
        0
    ])
    ctx = OSMesaCreateContextAttribs(attrs, None)
    # ctx = OSMesaCreateContextExt(OSMESA_RGBA, 32, 0, 0, None)
    buf = arrays.GLubyteArray.zeros((width, height, 4))
    assert (OSMesaMakeCurrent(ctx, buf, GL.GL_UNSIGNED_BYTE, width, height))
    assert (OSMesaGetCurrentContext())

    z = GL.glGetIntegerv(GL.GL_DEPTH_BITS)
    s = GL.glGetIntegerv(GL.GL_STENCIL_BITS)
    a = GL.glGetIntegerv(GL.GL_ACCUM_RED_BITS)
    print("Depth=%d Stencil=%d Accum=%d" % (z, s, a))

    print("Width=%d Height=%d" % (OSMesaGetIntegerv(OSMESA_WIDTH),
                                  OSMesaGetIntegerv(OSMESA_HEIGHT)))
    return ctx, buf


def free_ctx(ctx, buf):
    GL.glFinish()
    write_ppm(buf, 'osmesa_output.ppm')
    write_image(buf, 'osmesa_output.jpeg')
    OSMesaDestroyContext(ctx)


def _do_opengl_drawing(height, width):
    GL.glViewport(0, 0, width, height)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glClearColor(0.2, 0.4, 0.6, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    # gluPerspective(45.0, width / float(height), 0.1, 100.0)
    # Draw a simple triangle
    GL.glBegin(GL.GL_TRIANGLES)
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glVertex2f(-0.6, -0.4)
    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glVertex2f(0.6, -0.4)
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glVertex2f(0.0, 0.6)
    GL.glEnd()
    GL.glFlush()
    _opengl_context_info()


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
    set_true_for_segfault = True
    print(os.path.join(here, 'sphere.exf'), os.path.isfile(os.path.join(here, 'sphere.exf')), os.path.getsize(os.path.join(here, 'sphere.exf')))
    res = r.readFile(os.path.join(here, 'sphere.exf')) if set_true_for_segfault else 0
    print("Read file result:", res)
    s = r.getScene()
    print("Zinc scene:", s.isValid())
    sceneviewer.setScene(s)
    res = s.readDescription(json.dumps(t), True)
    print("Read description result:", res)
    res = sceneviewer.readDescription(json.dumps(sv))
    print("Sceneviewer read description result:", res, flush=True)
    sceneviewer.setRenderTimeout(-1.0)
    _opengl_context_info()
    sceneviewer.renderScene()
    # sceneviewer.writeImageToFile('osmesa_output.jpeg', 0, width, height, 4, 0)
    return r


def _opengl_context_info():
    from OpenGL.GL.ARB import compatibility

    profile_mask = GL.glGetIntegerv(GL.GL_CONTEXT_PROFILE_MASK)

    if profile_mask & GL.GL_CONTEXT_CORE_PROFILE_BIT:
        print("OpenGL Core Profile")
    elif profile_mask & GL.GL_CONTEXT_COMPATIBILITY_PROFILE_BIT:
        print("OpenGL Compatibility Profile")
    else:
        print("Unknown or no profile")

    print("OpenGL Version:", GL.glGetString(GL.GL_VERSION))
    print("GLSL Version:", GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION))
    print("Vendor:", GL.glGetString(GL.GL_VENDOR))
    print("Renderer:", GL.glGetString(GL.GL_RENDERER), flush=True)


if __name__ == "__main__":
    # main()
    print("Starting offscreen rendering with OSMesa...")
    print(os.environ.get('PYOPENGL_PLATFORM'))
    print(os.environ.get('LIBGL_ALWAYS_SOFTWARE'))
    context, buffer = init_ctx(3260, 2048)
    print("Initialized OSMesa context and buffer.")
    _do_zinc_drawing(2048, 3260)
    # _do_opengl_drawing(2048, 3260)
    print("Zinc drawing completed.")
    free_ctx(context, buffer)
    print("Freed OSMesa context and buffer.")
    print("Rendered image saved as osmesa_output.jpeg")
