import pyglet
from pyglet.gl import *
from pyglet.window import key, mouse
import math
import threading
import os

# Window item for our pyglet's "base" to work off of!
window = pyglet.window.Window(width=800, height=800, caption='Pyglet 3D Example', resizable=True)

# Default values for application start
rot_x = 20.0   # rotation around X (degrees)
rot_y = -30.0  # rotation around Y (degrees)
distance = 7.0  # distance from camera to scene (positive)

startx, starty, startdist = rot_x, rot_y, distance

pan_x = 0.0
pan_y = 0.0
_last_mouse_x = 0
_last_mouse_y = 0

# Vector components to display
vector_x = 0.0
vector_y = 0.0
vector_z = 0.0

# Target components to translate to
target_x = vector_x
target_y = vector_y
target_z = vector_z

interpolation_speed = 0.1

# Lock for thread-safe access to vector variables
vector_lock = threading.Lock()

def menu_thread():
    """Background thread for handling terminal menu"""
    global target_x, target_y, target_z
    while True:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Hello, this is a prototype for CSC 4700's visualization problem here!")
            
            print("/" * 22)
            user_input = input("Enter vector as 'x y z' (or 'quit'): ")
            print("/" * 22)
            if user_input.strip().lower() == 'quit':
                pyglet.app.exit()
                break
            values = user_input.strip().split()
            if len(values) == 3:
                with vector_lock:
                    target_x = float(values[0])
                    target_y = float(values[1])
                    target_z = float(values[2])

                print(f"Target vector set to ({target_x}, {target_y}, {target_z})")
            else:
                print("Invalid format. Use: x y z")
        except (ValueError, EOFError):
            print("Invalid input, vector unchanged")

# Drawing horizontal grid base
def draw_grid(size=10, step=1.0):
    glLineWidth(1.0)
    glBegin(GL_LINES)
    glColor3f(0.3, 0.3, 0.3)  # Gray grid lines
    
    half_size = size / 2.0
    num_lines = int(size / step) + 1
    
    # Lines parallel to X axis
    for i in range(num_lines):
        z = -half_size + i * step
        glVertex3f(-half_size, 0.0, z)
        glVertex3f(half_size, 0.0, z)
    
    # Lines parallel to Z axis
    for i in range(num_lines):
        x = -half_size + i * step
        glVertex3f(x, 0.0, -half_size)
        glVertex3f(x, 0.0, half_size)
    
    glEnd()

    # Draw axes (X=red, Y=green, Z=blue)
    glLineWidth(3.0)
    glBegin(GL_LINES)
    # X axis - red
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(2.0, 0.0, 0.0)
    
    # Y axis - green
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 2.0, 0.0)
    
    # Z axis - blue
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, 2.0)
    glEnd()


@window.event
def on_resize(width, height):
    # Set viewport and perspective projection
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Protect against height == 0
    aspect = width / float(height or 1)
    gluPerspective(45.0, aspect, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)  # Switch back to modelview
    glLoadIdentity()
    return pyglet.event.EVENT_HANDLED


@window.event
def on_draw():
    global rot_x, rot_y, distance, pan_x, pan_y, vector_x, vector_y, vector_z
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Apply camera transforms:
    glTranslatef(pan_x, pan_y, -distance)
    glRotatef(rot_x, 1.0, 0.0, 0.0)
    glRotatef(rot_y, 0.0, 1.0, 0.0)
    
    # Interpolate vector
    vector_x += (target_x - vector_x) * interpolation_speed
    vector_y += (target_y - vector_y) * interpolation_speed
    vector_z += (target_z - vector_z) * interpolation_speed

    # Draw grid first (as background)
    draw_grid(size=10, step=1.0)
    
    # Draw your vector (the original line)
    glLineWidth(7.0)
    glBegin(GL_LINES)
    glColor3f(1.0, 1.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(vector_x, vector_y, vector_z)
    glEnd()


@window.event
def on_mouse_press(x, y, button, modifiers):
    global _last_mouse_x, _last_mouse_y
    _last_mouse_x = x
    _last_mouse_y = y


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    """
    Left-drag: rotate
    Right-drag: pan
    """
    global rot_x, rot_y, pan_x, pan_y, _last_mouse_x, _last_mouse_y

    # Sensitivity constants
    rotate_sens = 0.3
    pan_sens = 0.005 * distance

    if buttons & mouse.LEFT:
        # Rotate: drag horizontally -> rot_y, vertically -> rot_x
        rot_y += dx * rotate_sens
        rot_x += dy * rotate_sens
        # Clamp X rotation to avoid flipping
        rot_x = max(-90.0, min(90.0, rot_x))
    elif buttons & mouse.RIGHT:
        # Pan: move in screen X/Y
        pan_x += dx * pan_sens
        pan_y -= dy * pan_sens  # invert Y

    _last_mouse_x = x
    _last_mouse_y = y


@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    """
    Zoom in/out with scroll wheel.
    """
    global distance
    zoom_sens = 0.5
    distance -= scroll_y * zoom_sens
    # Clamp distance to reasonable bounds
    distance = max(0.5, min(50.0, distance))


@window.event
def on_key_press(symbol, modifiers):
    global rot_x, rot_y, distance, pan_x, pan_y, vector_x, vector_y, vector_z, target_x, target_y, target_z
    if symbol == key.R:
        # Reset view
        rot_x = startx
        rot_y = starty
        distance = startdist
        pan_x = 0.0
        pan_y = 0.0
    # elif symbol == key.ESCAPE:
    #     window.close()

    
def update(dt):
    pass  # Triggers continuous redraw for smooth interpolation


if __name__ == "__main__":
    # GL setup
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.1, 0.1, 0.1, 1.0)

    # Start input thread
    thread = threading.Thread(target=menu_thread, daemon=True)
    thread.start()


    pyglet.clock.schedule_interval(update, 1/30.0)

    pyglet.app.run()