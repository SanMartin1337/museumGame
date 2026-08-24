from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()
window.fullscreen = True
render.setShaderAuto()

def rgba255(r, g, b, a=255):
    return color.rgba(r / 255, g / 255, b / 255, a / 255)

floor = Entity(model='plane', scale=(20, 1, 20), color=color.white, collider='box')
wall = Entity(model='cube', scale=(20, 4, 0.3), position=(0, 2, 5), color=color.white, collider='box')

amb = AmbientLight(color=rgba255(4, 4, 7, 255))
print('AmbientLight создан:', amb)
print('цвет ambient:', amb.color)

player = FirstPersonController(position=(0, 1, -5))

app.run()