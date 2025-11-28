import pyglet
from pyglet.gl import *
from pyglet.window import key, mouse
import math
import threading
import os
import time

from vector_utils import slerp_via_axis
from button import Button
from constants import WINDOW_WIDTH, WINDOW_HEIGHT

# Window item for our pyglet's "base" to work off of!
window = pyglet.window.Window(width=WINDOW_WIDTH, height=WINDOW_HEIGHT, caption='Pyglet 3D Example', resizable=False)

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
vector_z = 1.0

# Target components to translate to
target_x = vector_x
target_y = vector_y
target_z = vector_z

interpolation_speed = 0.02
interpolation_t = 1.0  # Interpolation parameter (0 to 1)
rotation_phase = 0.0  # Phase between X (0.0) and Y (1.0) axis

# State management
states_list = []
current_state_index = 0

buttons = []


def prev_state():
    global current_state_index, target_x, target_y, target_z, rotation_phase, interpolation_t
    if len(states_list) > 0 and current_state_index > 0:
        current_state_index -= 1
        state = states_list[current_state_index]
        with vector_lock:
            target_x = state[0]
            target_y = state[1]
            target_z = state[2]
            rotation_phase = state[3]
            interpolation_t = 0.0

def next_state():
    global current_state_index, target_x, target_y, target_z, rotation_phase, interpolation_t
    if len(states_list) > 0 and current_state_index < len(states_list) - 1:
        current_state_index += 1
        state = states_list[current_state_index]
        with vector_lock:
            target_x = state[0]
            target_y = state[1]
            target_z = state[2]
            rotation_phase = state[3]
            interpolation_t = 0.0

def reset_state():
    global current_state_index, target_x, target_y, target_z, rotation_phase, interpolation_t
    if len(states_list) > 0:
        current_state_index = 0
        state = states_list[0]
        with vector_lock:
            target_x = state[0]
            target_y = state[1]
            target_z = state[2]
            rotation_phase = state[3]
            interpolation_t = 0.0

# Lock for thread-safe access to vector variables
vector_lock = threading.Lock()

def menu_thread(states=[]):
    """Background thread for handling terminal menu"""
    global target_x, target_y, target_z, interpolation_t, rotation_phase
    
    time.sleep(1)
    for state in states:
        with vector_lock:
            target_x = state[0]
            target_y = state[1]
            target_z = state[2]
            rotation_phase = state[3]
            interpolation_t = 0.0
        
        # Wait until interpolation is done
        while True:
            with vector_lock:
                if interpolation_t >= 1.0:
                    break
            time.sleep(0.1)

def draw_circle(radius, segments=32, axis='z'):
    """Draw a circle around the specified axis"""
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        
        if axis == 'z':  # Circle in XY plane
            glVertex3f(x, 0.0, y)
        elif axis == 'y':  # Circle in XZ plane
            glVertex3f(x, y, 0.0)
        elif axis == 'x':  # Circle in YZ plane
            glVertex3f(0.0, x, y)
    glEnd()

def draw_bloch_sphere(radius=1.0):
    """Draw a Bloch sphere with meridians and equator"""
    glLineWidth(1.5)
    
    # Draw equator
    glColor3f(0.5, 0.5, 0.5)
    draw_circle(radius, segments=64, axis='z')
    
    # Draw prime meridian
    glColor3f(0.4, 0.4, 0.4)
    draw_circle(radius, segments=64, axis='y')
    
    # Draw another meridian
    glColor3f(0.4, 0.4, 0.4)
    draw_circle(radius, segments=64, axis='x')
    
    
    # Draw axes through sphere
    glLineWidth(2.5)
    glBegin(GL_LINES)
    # X axis
    glColor3f(0.8, 0.2, 0.2)
    glVertex3f(-radius * 1.2, 0.0, 0.0)
    glVertex3f(radius * 1.2, 0.0, 0.0)
    
    # Y axis
    glColor3f(0.2, 0.2, 0.8)
    glVertex3f(0.0, 0.0, -radius * 1.2)
    glVertex3f(0.0, 0.0, radius * 1.2)
    
    # Z axis
    glColor3f(0.2, 0.8, 0.2)
    glVertex3f(0.0, -radius * 1.2, 0.0)
    glVertex3f(0.0, radius * 1.2, 0.0)
    glEnd()


def draw_state_vector(vector_x, vector_y, vector_z):
    """Draw the quantum state vector with arrowhead, extending beyond the Bloch sphere"""

    vec_length = math.sqrt(vector_x**2 + vector_y**2 + vector_z**2)
    if vec_length > 1e-6:
        # Normalize
        norm_x = vector_x / vec_length
        norm_y = vector_y / vec_length
        norm_z = vector_z / vec_length
        
        # Extend by 15% beyond unit sphere to see the arrow
        extended_x = norm_x * 1.15
        extended_y = norm_y * 1.15
        extended_z = norm_z * 1.15
    else:
        extended_x, extended_y, extended_z = vector_x, vector_y, vector_z
    
    # Draw state vector
    glLineWidth(4.0)
    glBegin(GL_LINES)
    glColor3f(1.0, 0.8, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(extended_x, extended_z, extended_y)

    # draw arrow
    arrow_length = 0.1
    dir_x = extended_x
    dir_y = extended_z
    dir_z = extended_y
    vec_length_ext = math.sqrt(dir_x**2 + dir_y**2 + dir_z**2)

    if vec_length_ext > 1e-6:
        dir_x /= vec_length_ext
        dir_y /= vec_length_ext
        dir_z /= vec_length_ext

        base_x = extended_x - dir_x * arrow_length
        base_y = extended_z - dir_y * arrow_length
        base_z = extended_y - dir_z * arrow_length

        # Create two perpendicular vectors for the arrowhead wings
        up_x, up_y, up_z = 0.0, 1.0, 0.0
        if abs(dir_x) < 1e-6 and abs(dir_z) < 1e-6:
            up_x, up_y, up_z = 1.0, 0.0, 0.0  # Change up vector if pointing along Y

        # Cross product to get a perpendicular vector
        perp_x = dir_y * up_z - dir_z * up_y
        perp_y = dir_z * up_x - dir_x * up_z
        perp_z = dir_x * up_y - dir_y * up_x

        # Normalize perpendicular vector
        perp_length = math.sqrt(perp_x**2 + perp_y**2 + perp_z**2)
        if perp_length > 1e-6:
            perp_x /= perp_length
            perp_y /= perp_length
            perp_z /= perp_length

            wing_span = arrow_length * 0.5

            # Left wing
            glVertex3f(extended_x, extended_z, extended_y)
            glVertex3f(base_x + perp_x * wing_span, base_y + perp_y * wing_span, base_z + perp_z * wing_span)
            # Right wing
            glVertex3f(extended_x, extended_z, extended_y)
            glVertex3f(base_x - perp_x * wing_span, base_y - perp_y * wing_span, base_z - perp_z * wing_span)

    glEnd()


def project_3d_to_2d(x, y, z):
    """Project 3D world coordinates to 2D screen coordinates"""
    # Get the current model, projection, and viewport matrices
    modelview = (GLdouble * 16)()
    projection = (GLdouble * 16)()
    viewport = (GLint * 4)()
    
    glGetDoublev(GL_MODELVIEW_MATRIX, modelview)
    glGetDoublev(GL_PROJECTION_MATRIX, projection)
    glGetIntegerv(GL_VIEWPORT, viewport)
    
    # Project the 3D point
    win_x = GLdouble()
    win_y = GLdouble()
    win_z = GLdouble()
    
    gluProject(x, y, z, modelview, projection, viewport, win_x, win_y, win_z)
    
    return int(win_x.value), int(win_y.value)


def draw_axis_labels():
    """Draw the X, Y, Z axis labels in 2D screen space"""
    # Project 3D axis endpoints to 2D screen coordinates for labels
    x_pos = project_3d_to_2d(1.4, 0.0, 0.0)
    y_pos = project_3d_to_2d(0.0, 0.0, 1.4)
    z_pos = project_3d_to_2d(0.0, 1.4, 0.0)
    
    # Switch to 2D mode for text rendering
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window.width, 0, window.height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth test for text
    glDisable(GL_DEPTH_TEST)
    
    # Create labels for axis markers
    x_label = pyglet.text.Label('X', font_size=14, x=0, y=0, color=(255, 0, 0, 255))
    y_label = pyglet.text.Label('Y', font_size=14, x=0, y=0, color=(0, 0, 255, 255))
    z_label = pyglet.text.Label('Z', font_size=14, x=0, y=0, color=(0, 255, 0, 255))

    # Draw the axis labels
    x_label.x, x_label.y = x_pos
    x_label.draw()
    
    y_label.x, y_label.y = y_pos
    y_label.draw()
    
    z_label.x, z_label.y = z_pos
    z_label.draw()
    
    # Re-enable depth test and restore matrices
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def init_buttons():
    prev_button = Button(20, 20, 40, 40, "<", prev_state)
    next_button = Button(70, 20, 40, 40, ">", next_state)
    reset_button = Button(120, 20, 100, 40, "Reset", reset_state)
    buttons.extend([prev_button, next_button, reset_button])


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
    global rot_x, rot_y, distance, pan_x, pan_y, vector_x, vector_y, vector_z, interpolation_t
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Apply camera transforms:
    glTranslatef(pan_x, pan_y, -distance)
    glRotatef(rot_x, 1.0, 0.0, 0.0)
    glRotatef(rot_y, 0.0, 1.0, 0.0)
    
    # Store the starting position for SLERP
    start_x, start_y, start_z = vector_x, vector_y, vector_z
    
    # Update interpolation parameter
    if interpolation_t < 1.0:
        interpolation_t = min(1.0, interpolation_t + interpolation_speed)
        
        # Compute rotation vector based on phase (blend between X and Y)
        phase_x = 1.0 - rotation_phase  # More X at phase=0
        phase_y = rotation_phase         # More Y at phase=1
        rotation_vector = (phase_x, phase_y, 0.0)
        
        # Use SLERP with the computed rotation vector
        vector_x, vector_y, vector_z = slerp_via_axis(
            start_x, start_y, start_z,
            target_x, target_y, target_z,
            interpolation_t,
            via_vector=rotation_vector
        )

    draw_bloch_sphere(radius=1.0)
    
    draw_state_vector(vector_x, vector_y, vector_z)
    
    draw_axis_labels()

    for button in buttons:
        button.draw()
    

@window.event
def on_mouse_press(x, y, button, modifiers):
    global _last_mouse_x, _last_mouse_y
    _last_mouse_x = x
    _last_mouse_y = y
    
    # Check if any button was clicked
    if button == mouse.LEFT:
        for btn in buttons:
            if btn.contains(x, y):
                btn.action()
                return


@window.event
def on_mouse_motion(x, y, dx, dy):
    """Handle mouse motion for button hover effects"""
    for btn in buttons:
        btn.hovered = btn.contains(x, y)


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


def visualize(states):
    global states_list, current_state_index, target_x, target_y, target_z, rotation_phase, interpolation_t
    states_list = [[0.0, 0.0, 0.1, 0.0]] + states
    
    # Initialize to first state if available
    if len(states_list) > 0:
        current_state_index = 0
        state = states_list[0]
        target_x = state[0]
        target_y = state[1]
        target_z = state[2]
        rotation_phase = state[3]
        interpolation_t = 0.0

    init_buttons()
    
    # thread = threading.Thread(target=menu_thread, args=(states,), daemon=True)
    # thread.start()

    pyglet.clock.schedule_interval(update, 1/30.0)

    pyglet.app.run()

if __name__ == "__main__":
    # GL setup
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.1, 0.1, 0.1, 1.0)

    # Example states to visualize
    states = [
                [1.0, 0.0, 0.0, 0.5],
                [0.0, 1.0, 0.0, 1.0],
                [1.0, 0.0, 1.0, 0.0]
            ]
    
    visualize(states)

