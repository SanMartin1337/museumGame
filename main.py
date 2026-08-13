from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
# создаем движок / старт
app = Ursina()

# делаем полноэкранный режим
window.fullscreen = True

floor = Entity(
    model='plane',
    scale=(20,1,20),
    position=(0, -0.5, 0),
    color = color.gray,
    collider='box',
)

# создаем персонажа который и может ходить WASD
player = FirstPersonController(position=(0, 1, -5))
# главный цикл запуск
app.run()

