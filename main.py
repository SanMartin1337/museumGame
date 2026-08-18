from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from objects import (Flashlight, Desk, Monitor, Chair, Locker, LockerUI,
                     has_model, load_furniture, FURNITURE_SIZES)
from PIL import Image
import os

for tex in ('floor', 'wall', 'ceiling'):
    found = any(os.path.exists(f'{tex}.{e}') for e in ('png', 'jpg', 'jpeg'))
    print(f'текстура {tex}:', 'найдена' if found else 'НЕ НАЙДЕНА')

app = Ursina()
window.fullscreen = True
window.vsync = False
render.setShaderAuto()

# пол: комната 8.4 x 7 (было 12 x 10), повтор текстуры реже - ламинат крупнее
floor = Entity(
    model='plane', scale=(8.4, 1, 7), position=(0, -0.5, 0),
    color=color.white, texture='floor', collider='box',
)
floor.texture_scale = (1.5, 1.5)

# стены с текстурой (wall.png рядом с main.py)
wall_back = Entity(model='cube', scale=(8.4, 4, 0.3), position=(0, 1.5, 3.5),
                   color=color.white, texture='wall', collider='box')
wall_front = Entity(model='cube', scale=(8.4, 4, 0.3), position=(0, 1.5, -3.5),
                    color=color.white, texture='wall', collider='box')
wall_left = Entity(model='cube', scale=(0.3, 4, 7), position=(-4.2, 1.5, 0),
                   color=color.white, texture='wall', collider='box')
wall_right = Entity(model='cube', scale=(0.3, 4, 7), position=(4.2, 1.5, 0),
                    color=color.white, texture='wall', collider='box')
for w in (wall_back, wall_front, wall_left, wall_right):
    w.texture_scale = (3, 1.5)


# потолок БЕЗ unlit - он будет освещаться как настоящий
# потолок - твои белые плиты, unlit
ceiling = Entity(
    model='plane', scale=(8.4, 1, 7), position=(0, 3.5, 0),
    rotation=(180, 0, 0), texture='ceiling_dark',
    double_sided=True, unlit=True,
)
ceiling.texture_scale = (1, 1)

# полупрозрачная тёмная плёнка чуть ниже - приглушает потолок
# плиты и решётка видны, но уже не слепят



# свет с потолка: источник невидимый, белого куба больше нет
lamp_spot = SpotLight(position=(0, 3.3, 0), color=color.rgba(200, 190, 160, 255))
lamp_spot._light.setAttenuation(Vec3(1, 0.2, 0.1))
lamp_spot._light.getLens().setFov(90)

# очень тусклый ambient
AmbientLight(color=color.rgba(30, 30, 40, 255))

# холодный свет от мониторов
monitor_glow = PointLight(
    position=(0, 1.2, 2.5),
    color=color.rgba(120, 160, 220, 255),
)
monitor_glow._light.setAttenuation(Vec3(1, 0.3, 0.15))

# === МЕБЕЛЬ ОХРАННИКА (позиции под ужатыю комнату) ===

desk = Desk((0, -0.5, 2.9))

# боковые мониторы довёрнуты к центру
monitor_l = Monitor(-0.85, 2.9, desk.top_y, tilt=-20, screen_color=color.rgba(90, 130, 170))
monitor_c = Monitor(0, 2.9, desk.top_y, screen_color=color.rgba(120, 160, 200))
monitor_r = Monitor(0.85, 2.9, desk.top_y, tilt=20, screen_color=color.rgba(90, 130, 170))

# клавиатура
if has_model('keyboard'):
    size, axis = FURNITURE_SIZES['keyboard']
    keyboard = load_furniture('keyboard', size, 0, 2.5, desk.top_y, axis=axis)
else:
    keyboard = Entity(model='cube', scale=(0.5, 0.03, 0.2),
                      position=(0, desk.top_y + 0.02, 2.5),
                      color=color.rgba(25, 25, 25), collider='box')

# кресло за спиной
# кресло крупнее и левее
chair = Chair((-0.6, -0.5, 1.0))

# шкаф за креслом (если встанет спиной - rotation_y=180)
locker = Locker((-0.6, -0.5, -3.1), rotation_y=0)

# окно хранилища
locker_ui = LockerUI()
# игрок
player = FirstPersonController(position=(0, 1, 1.6), speed=5)



# фонарик
flashlight = Flashlight()

# UI
battery_bar = Entity(
    parent=camera.ui, model='quad', scale=(0.3, 0.02),
    position=(-0.35, -0.45), color=color.rgba(80, 80, 80, 255), unlit=True,
)
battery_fill = Entity(
    parent=camera.ui, model='quad', scale=(0.3, 0.02),
    position=(-0.35, -0.45), color=color.rgba(100, 200, 100, 255), unlit=True,
)
hint_text = Text(
    parent=camera.ui, text='F - фонарик | E - хранилище',
    position=(-0.85, -0.48), scale=1.2,
    color=color.rgba(200, 200, 200, 255),
)


def update():
    # пока хранилище открыто - игрок стоит на месте
    player.speed = 0 if locker_ui.open else 5
    dt = time.dt
    flashlight.update(dt)

    # полоска батарейки
    battery_fill.scale_x = 0.3 * (flashlight.battery / flashlight.max_battery)
    if flashlight.battery < 20:
        battery_fill.color = color.rgba(200, 50, 50, 255)
    elif flashlight.battery < 50:
        battery_fill.color = color.rgba(200, 200, 50, 255)
    else:
        battery_fill.color = color.rgba(100, 200, 100, 255)

    # мерцание экранов (только для запасных мониторов)
    if monitor_c.screen is not None:
        flicker = 0.9 + 0.1 * abs(sin(time.time() * 13))
        monitor_c.screen.color = color.rgba(
            int(120 * flicker), int(160 * flicker), int(200 * flicker)
        )


def input(key):
    if key == 'f':
        flashlight.toggle()

    # E - открыть/закрыть хранилище (открывается только рядом со шкафом)
    if key == 'e':
        if locker_ui.open:
            locker_ui.close_ui()
        elif locker.player_near(player):
            locker_ui.open_ui()

    # Escape закрывает окно
    if key == 'escape' and locker_ui.open:
        locker_ui.close_ui()
app.run()