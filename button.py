from pyglet.gl import *
import pyglet
from constants import WINDOW_WIDTH, WINDOW_HEIGHT


class Button:
    def __init__(self, x, y, width, height, text, action):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.action = action
        self.label = pyglet.text.Label(text, font_size=12, x=x + width//2, y=y + height//2,
                                       anchor_x='center', anchor_y='center',
                                       color=(255, 255, 255, 255))
        self.hovered = False
    
    def contains(self, x, y):
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def draw(self):
        # Draw button background and border
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Button color (darker when hovered)
        if self.hovered:
            glColor4f(0.3, 0.3, 0.5, 0.9)
        else:
            glColor4f(0.2, 0.2, 0.4, 0.8)
        
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()
        
        # Button border
        glColor3f(0.6, 0.6, 0.8)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()
        
        # Keep 2D projection for label
        # Draw label on top (still in 2D mode)
        glColor4f(1.0, 1.0, 1.0, 1.0)  # Reset color to white for text
        self.label.draw()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)