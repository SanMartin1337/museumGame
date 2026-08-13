from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
# создаем движок / старт
app = Ursina()
from ursina.shaders import lit_with_shadows_shader
Entity.default_shader = lit_with_shadows_shader
# делаем полноэкранный режим
window.fullscreen = True
window.vsync = False
floor = Entity(
    model='plane',
    scale=(12, 1, 10),
    position=(0, -0.5, 0),
    color=color.dark_gray,
    collider='box',
)
# создаем стены (комнату охранника)
wall_back = Entity(model='cube', scale=(12, 4, 0.3), position=(0, 1.5, 5), color=color.gray, collider='box')
wall_front = Entity(model='cube', scale=(12, 4, 0.3), position=(0, 1.5, -5), color=color.gray, collider='box')
wall_left = Entity(model='cube', scale=(0.3, 4, 10), position=(-6, 1.5, 0), color=color.gray, collider='box')
wall_right = Entity(model='cube', scale=(0.3, 4, 10), position=(6, 1.5, 0), color=color.gray, collider='box')
# потолок
ceiling = Entity(
    model='plane',
    scale=(12, 1, 10),
    position=(0, 3.5, 0),
    rotation=(180, 0, 0),
    color=color.dark_gray,
    double_sided=True,
)

# типа лампочки
lamp1 = Entity(model='cube', scale=(1.5, 0.15, 0.4), position=(-3, 3.4, 0), color=color.white)
lamp2 = Entity(model='cube', scale=(1.5, 0.15, 0.4), position=(3, 3.4, 0), color=color.white)

# источник света
lamp_light = PointLight(position=(-3, 2.0, 0), color=color.rgba(80, 70, 55, 255))
lamp_light._light.setAttenuation(Vec3(1, 0, 100))
#PointLight(position=(3, 3.2, 0), color=color.rgba(80, 70, 55, 255), radius=6)
AmbientLight(color=color.rgba(40, 40, 50, 255))
# создаем персонажа который и может ходить WASD
player = FirstPersonController(position=(0, 1, 0))
# главный цикл запуск
app.run()

