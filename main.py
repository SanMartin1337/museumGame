from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from objects import (Flashlight, Desk, Monitor, Chair, Locker, LockerUI,
                     has_model, load_furniture, FURNITURE_SIZES, rgba255,
                     Hotbar, Inventory)
from PIL import Image
import os

for tex in ('floor', 'wall', 'ceiling'):
    found = any(os.path.exists(f'{tex}.{e}') for e in ('png', 'jpg', 'jpeg'))
    print(f'текстура {tex}:', 'найдена' if found else 'НЕ НАЙДЕНА')

app = Ursina()
window.fullscreen = True
window.vsync = False
render.setShaderAuto()

# сколько игровых юнитов занимает ОДИН повтор текстуры - подобрано по
# исходной большой стене/полу, чтобы плитка/кирпич были одного размера
# на любом куске стены или пола, а не "сжимались" на узких кусках
WALL_TILE_X = 2.8
WALL_TILE_Y = 4 / 1.5  # исходная высота стены (4) делённая на исходный повтор (1.5)
FLOOR_TILE_X = 8.4 / 1.5  # исходная ширина пола делённая на исходный повтор
FLOOR_TILE_Z = 7 / 1.5    # исходная глубина пола делённая на исходный повтор


def set_wall_texture_scale(entity, width, height):
    """Ставит texture_scale так, чтобы размер кирпича был одинаковым
    на любой стене, независимо от её реальной ширины/высоты."""
    entity.texture_scale = (width / WALL_TILE_X, height / WALL_TILE_Y)


def set_floor_texture_scale(entity, width, depth):
    """То же самое, но для пола/потолка."""
    entity.texture_scale = (width / FLOOR_TILE_X, depth / FLOOR_TILE_Z)

# пол: комната 8.4 x 7 (было 12 x 10), повтор текстуры реже - ламинат крупнее
floor = Entity(
    model='plane', scale=(8.4, 1, 7), position=(0, -0.5, 0),
    color=color.white, texture='floor', collider='box',
)
set_floor_texture_scale(floor, 8.4, 7)

# стены с текстурой (wall.png рядом с main.py)
wall_back = Entity(model='cube', scale=(8.4, 4, 0.3), position=(0, 1.5, 3.5),
                   color=color.white, texture='wall', collider='box')
wall_front = Entity(model='cube', scale=(8.4, 4, 0.3), position=(0, 1.5, -3.5),
                    color=color.white, texture='wall', collider='box')
wall_left = Entity(model='cube', scale=(0.3, 4, 7), position=(-4.2, 1.5, 0),
                   color=color.white, texture='wall', collider='box')

# правая стена с дверным проёмом посередине (ширина проёма 1.2, от z=-0.6 до z=0.6)
wall_right_a = Entity(model='cube', scale=(0.3, 4, 2.9), position=(4.2, 1.5, -2.05),
                      color=color.white, texture='wall', collider='box')
wall_right_b = Entity(model='cube', scale=(0.3, 4, 2.9), position=(4.2, 1.5, 2.05),
                      color=color.white, texture='wall', collider='box')
# перемычка над проёмом (дверь высотой 2.1, стена высотой 4 - сверху остаётся дыра, глушим её)
door_lintel = Entity(model='cube', scale=(0.3, 1.9, 1.2), position=(4.2, 3.05, 0),
                     color=color.white, texture='wall', collider='box')
wall_right = wall_right_a  # чтобы не сломать цикл текстур ниже (просто ссылка)

set_wall_texture_scale(wall_back, 8.4, 4)
set_wall_texture_scale(wall_front, 8.4, 4)
set_wall_texture_scale(wall_left, 7, 4)
set_wall_texture_scale(wall_right_a, 2.9, 4)
set_wall_texture_scale(wall_right_b, 2.9, 4)
set_wall_texture_scale(door_lintel, 1.2, 1.9)


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
lamp_spot = SpotLight(position=(0, 3.3, 0), color=rgba255(200, 190, 160, 255))
lamp_spot._light.setAttenuation(Vec3(1, 0.2, 0.1))
lamp_spot._light.getLens().setFov(90)

# очень тусклый ambient
AmbientLight(color=rgba255(30, 30, 40, 255))

# холодный свет от мониторов
monitor_glow = PointLight(
    position=(0, 1.2, 2.5),
    color=rgba255(120, 160, 220, 255),
)
monitor_glow._light.setAttenuation(Vec3(1, 0.3, 0.15))

# === КОРИДОР ЗА ДВЕРЬЮ ===
# проём в правой стене на x=4.2, ширина проёма по z: -0.6..0.6
# коридор тянется дальше по x, узкий (ширина по z всего 1.6)

corridor_length = 5
corridor_start_x = 4.35  # чуть дальше стены (толщина стены 0.3, половина 0.15)
corridor_center_x = corridor_start_x + corridor_length / 2

corridor_floor = Entity(
    model='plane', scale=(corridor_length, 1, 1.6),
    position=(corridor_center_x, -0.5, 0),
    color=color.white, texture='floor', collider='box',
)
set_floor_texture_scale(corridor_floor, corridor_length, 1.6)

corridor_ceiling = Entity(
    model='plane', scale=(corridor_length, 1, 1.6),
    position=(corridor_center_x, 3.5, 0), rotation=(180, 0, 0),
    texture='ceiling_dark', double_sided=True, unlit=True,
)

corridor_wall_far = Entity(
    model='cube', scale=(corridor_length, 4, 0.3),
    position=(corridor_center_x, 1.5, 0.8),
    color=color.white, texture='wall', collider='box',
)
corridor_wall_near = Entity(
    model='cube', scale=(corridor_length, 4, 0.3),
    position=(corridor_center_x, 1.5, -0.8),
    color=color.white, texture='wall', collider='box',
)
corridor_wall_end = Entity(
    model='cube', scale=(0.3, 4, 1.6),
    position=(corridor_start_x + corridor_length, 1.5, 0),
    color=color.white, texture='wall', collider='box',
)
set_wall_texture_scale(corridor_wall_far, corridor_length, 4)
set_wall_texture_scale(corridor_wall_near, corridor_length, 4)
# в торцевой стене коридора оставляем проём в зал (без коллайдера - тут не дверь, просто арка)
corridor_wall_end.collider = None
corridor_wall_end.visible = False

corridor_light = PointLight(position=(corridor_center_x, 3.2, 0), color=rgba255(90, 85, 100, 255))
corridor_light._light.setAttenuation(Vec3(1, 0.15, 0.08))

# === ГЛАВНЫЙ ЗАЛ (примерно в 6 раз больше комнаты охранника по площади) ===
# комната охранника: 8.4 x 7 = 58.8 кв.юнитов -> зал: 20 x 17.5 = 350 (примерно x6)
HALL_W = 20   # по x
HALL_D = 17.5  # по z
HALL_H = 6     # повыше, чтобы ощущался как большой зал, а не просто растянутая комната

hall_start_x = corridor_start_x + corridor_length  # сразу за торцом коридора
hall_center_x = hall_start_x + HALL_W / 2

hall_floor = Entity(
    model='plane', scale=(HALL_W, 1, HALL_D),
    position=(hall_center_x, -0.5, 0),
    color=color.white, texture='floor', collider='box',
)
set_floor_texture_scale(hall_floor, HALL_W, HALL_D)

hall_ceiling = Entity(
    model='plane', scale=(HALL_W, 1, HALL_D),
    position=(hall_center_x, HALL_H - 0.5, 0), rotation=(180, 0, 0),
    texture='ceiling_dark', double_sided=True, unlit=True,
)

hall_wall_far = Entity(
    model='cube', scale=(HALL_W, HALL_H, 0.3),
    position=(hall_center_x, HALL_H / 2 - 0.5, HALL_D / 2),
    color=color.white, texture='wall', collider='box',
)
hall_wall_near = Entity(
    model='cube', scale=(HALL_W, HALL_H, 0.3),
    position=(hall_center_x, HALL_H / 2 - 0.5, -HALL_D / 2),
    color=color.white, texture='wall', collider='box',
)
hall_wall_end = Entity(
    model='cube', scale=(0.3, HALL_H, HALL_D),
    position=(hall_start_x + HALL_W, HALL_H / 2 - 0.5, 0),
    color=color.white, texture='wall', collider='box',
)
# проём для входа из коридора - оставляем дыру шириной 1.6 по центру
hall_wall_start_a = Entity(
    model='cube', scale=(0.3, HALL_H, (HALL_D - 1.6) / 2),
    position=(hall_start_x, HALL_H / 2 - 0.5, HALL_D / 4 + 0.4),
    color=color.white, texture='wall', collider='box',
)
hall_wall_start_b = Entity(
    model='cube', scale=(0.3, HALL_H, (HALL_D - 1.6) / 2),
    position=(hall_start_x, HALL_H / 2 - 0.5, -HALL_D / 4 - 0.4),
    color=color.white, texture='wall', collider='box',
)
for w, width in ((hall_wall_far, HALL_W), (hall_wall_near, HALL_W),
                 (hall_wall_end, HALL_D),
                 (hall_wall_start_a, (HALL_D - 1.6) / 2), (hall_wall_start_b, (HALL_D - 1.6) / 2)):
    set_wall_texture_scale(w, width, HALL_H)

# несколько тусклых точечных светов вдоль зала, чтобы не было угольно-чёрным на весь пролёт
for i in range(3):
    hx = hall_start_x + HALL_W * (i + 1) / 4
    hl = PointLight(position=(hx, HALL_H - 1, 0), color=rgba255(80, 75, 90, 255))
    hl._light.setAttenuation(Vec3(1, 0.2, 0.1))

# === ДВЕРЬ НА ПЕТЛЕ ===
# "точка опоры" (pivot) стоит ровно на петле - на краю проёма (z=-0.6).
# Сама дверь - дочерний объект pivot'а, сдвинутый от него на половину
# своей ширины. Когда крутим pivot, дверь вращается вокруг ЕГО оси,
# а не своего собственного центра - получается как настоящая петля.
door_pivot = Entity(position=(4.2, 1.05, -0.6))
door = Entity(
    parent=door_pivot, model='cube', scale=(0.08, 2.1, 1.15),
    position=(0, 0, 0.575),  # сдвиг на половину ширины (1.15 / 2)
    color=rgba255(90, 70, 55, 255), collider='box',
)
door_open = False
DOOR_OPEN_ANGLE = 100  # градусов, насколько дверь распахивается

def toggle_door():
    global door_open
    door_open = not door_open
    target_angle = DOOR_OPEN_ANGLE if door_open else 0
    door_pivot.animate('rotation_y', target_angle, duration=0.6, curve=curve.out_quad)
    # пока дверь открыта - убираем коллайдер, чтобы через неё можно было пройти
    door.collider = None if door_open else 'box'

def player_near_door(player, radius=2.0):
    d = ((door_pivot.x - player.x) ** 2 + (door_pivot.z - player.z) ** 2) ** 0.5
    return d <= radius

# === МЕБЕЛЬ ОХРАННИКА (позиции под ужатыю комнату) ===

desk = Desk((0, -0.5, 2.9))

# боковые мониторы довёрнуты к центру
monitor_l = Monitor(-0.85, 2.9, desk.top_y, tilt=-20, screen_color=rgba255(90, 130, 170))
monitor_c = Monitor(0, 2.9, desk.top_y, screen_color=rgba255(120, 160, 200))
monitor_r = Monitor(0.85, 2.9, desk.top_y, tilt=20, screen_color=rgba255(90, 130, 170))

# клавиатура
if has_model('keyboard'):
    size, axis = FURNITURE_SIZES['keyboard']
    keyboard = load_furniture('keyboard', size, 0, 2.5, desk.top_y, axis=axis)
else:
    keyboard = Entity(model='cube', scale=(0.5, 0.03, 0.2),
                      position=(0, desk.top_y + 0.02, 2.5),
                      color=rgba255(25, 25, 25), collider='box')

# кресло за спиной
# кресло крупнее и левее
chair = Chair((-0.6, -0.5, 1.0))

# шкаф за креслом (если встанет спиной - rotation_y=180)
locker = Locker((-0.6, -0.5, -3.1), rotation_y=0)

# окно хранилища
locker_ui = LockerUI()
# игрок
player = FirstPersonController(position=(0, 1, 1.6), speed=5)

hotbar = Hotbar()
inventory = Inventory()



# фонарик
flashlight = Flashlight()

# UI
battery_bar = Entity(
    parent=camera.ui, model='quad', scale=(0.3, 0.02),
    position=(-0.35, -0.45), color=rgba255(80, 80, 80, 255), unlit=True,
)
battery_fill = Entity(
    parent=camera.ui, model='quad', scale=(0.3, 0.02),
    position=(-0.35, -0.45), color=rgba255(100, 200, 100, 255), unlit=True,
)
hint_text = Text(
    parent=camera.ui, text='F - фонарик | E - хранилище | Q - дверь | TAB - инвентарь | 1-5 - ячейка',
    position=(-0.85, 0.47), scale=1.2,
    color=rgba255(200, 200, 200, 255),
)


def update():
    # пока хранилище открыто - игрок стоит на месте
    player.speed = 0 if locker_ui.open else 5
    dt = time.dt
    flashlight.update(dt)

    # полоска батарейки
    battery_fill.scale_x = 0.3 * (flashlight.battery / flashlight.max_battery)
    if flashlight.battery < 20:
        battery_fill.color = rgba255(200, 50, 50, 255)
    elif flashlight.battery < 50:
        battery_fill.color = rgba255(200, 200, 50, 255)
    else:
        battery_fill.color = rgba255(100, 200, 100, 255)

    # мерцание экранов (только для запасных мониторов)
    if monitor_c.screen is not None:
        flicker = 0.9 + 0.1 * abs(sin(time.time() * 13))
        monitor_c.screen.color = rgba255(
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

    # Q - открыть/закрыть дверь (только если игрок рядом)
    if key == 'q' and player_near_door(player):
        toggle_door()

    # TAB - открыть/закрыть инвентарь
    if key == 'tab':
        inventory.toggle()

    # цифры 1-5 переключают ячейку хотбара
    if key in ('1', '2', '3', '4', '5'):
        hotbar.select(int(key) - 1)
app.run()