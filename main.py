from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os


# === РАЗМЕРЫ МЕБЕЛИ В МЕТРАХ ===
# (размер, по чему мерить: 'max' - наибольшая сторона, 'y' - высота)
# Меняй числа под свой вкус, если что-то кажется мелким/крупным
FURNITURE_SIZES = {
    'desk':     (2.6, 'max'),
    'monitor':  (0.65, 'y'),   # было 0.45 - стало заметно крупнее
    'keyboard': (0.4, 'max'),
    'chair':    (1.1, 'y'),
}


def has_model(name):
    """Проверяет, лежит ли модель в models/ или в корне проекта."""
    for folder in ('models', '.'):
        for ext in ('.glb', '.gltf', '.obj', '.bam'):
            if os.path.exists(os.path.join(folder, name + ext)):
                return True
    return False


# === ДИАГНОСТИКА: какие файлы реально лежат в папке ===
print('--- диагностика моделей ---')
if os.path.exists('models'):
    print('файлы в models/:', os.listdir('models'))
else:
    print('папки models/ нет!')
for name in FURNITURE_SIZES:
    status = 'найдена' if has_model(name) else 'НЕ НАЙДЕНА (соберу из кубов)'
    print(f'{name}: {status}')
print('---------------------------')


def load_furniture(name, target_size, x, z, base_y, rotation_y=0, collider=None, axis='max'):
    """
    Грузит модель, автоматически масштабирует и ставит так:
    низ на base_y, ЦЕНТР модели точно в точке (x, z).
    """
    e = Entity(model=name, rotation_y=rotation_y)

    # измеряем родной размер и подбираем масштаб
    b = e.get_tight_bounds()
    if b:
        mn, mx = b
        if axis == 'y':
            native = mx[1] - mn[1]
        else:
            native = max(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])
        if native > 0:
            e.scale = target_size / native
            print(f'{name}: масштаб {round(e.scale, 4)}')

    # ставим и выравниваем: низ на base_y, центр по x и z - в заданную точку
    e.position = (x, base_y, z)
    b = e.get_tight_bounds()
    if b:
        mn, mx = b
        center_x = (mn[0] + mx[0]) / 2
        center_z = (mn[2] + mx[2]) / 2
        e.x += x - center_x
        e.z += z - center_z
        e.y += base_y - mn[1]

    if collider:
        e.collider = collider
    return e


class Flashlight:
    """
    Фонарик игрока: конус света на камере, батарейка садится.
    """
    def __init__(self):
        self.on = False
        self.battery = 100.0
        self.max_battery = 100.0
        self.drain_rate = 2.0

        self.light = SpotLight(
            parent=camera,
            position=(0, -0.3, 0),
            color=color.rgba(255, 245, 220, 255),
            rotation=(90, 0, 0),
        )
        self.light._light.setAttenuation(Vec3(1, 0.15, 0.08))
        self.light._light.getLens().setFov(60)
        self.light.enabled = False

    def toggle(self):
        self.on = not self.on
        self.light.enabled = self.on

    def update(self, dt):
        if self.on and self.battery > 0:
            self.battery -= self.drain_rate * dt
            if self.battery <= 0:
                self.battery = 0
                self.on = False
                self.light.enabled = False


class Desk:
    """Стол охранника. Запоминает высоту столешницы."""
    def __init__(self, position):
        x, y, z = position
        if has_model('desk'):
            size, axis = FURNITURE_SIZES['desk']
            self.entity = load_furniture('desk', size, x, z, -0.5, collider='box', axis=axis)
            b = self.entity.get_tight_bounds()
            self.top_y = b[1][1] if b else 0.26
            return

        # запасной вариант из кубов
        self.top = Entity(model='cube', scale=(2.6, 0.08, 1.0),
                          position=(x, y + 0.72, z),
                          color=color.rgba(70, 50, 35), collider='box')
        self.leg_l = Entity(model='cube', scale=(0.08, 0.72, 0.9),
                            position=(x - 1.2, y + 0.36, z),
                            color=color.rgba(40, 40, 40), collider='box')
        self.leg_r = Entity(model='cube', scale=(0.08, 0.72, 0.9),
                            position=(x + 1.2, y + 0.36, z),
                            color=color.rgba(40, 40, 40), collider='box')
        self.top_y = y + 0.76


class Monitor:
    """Монитор. Стоит на столешнице и смотрит на игрока."""
    def __init__(self, x, z, top_y, screen_color=color.rgba(110, 150, 190)):
        if has_model('monitor'):
            size, axis = FURNITURE_SIZES['monitor']
            # rotation_y=90 разворачивает модель экраном к игроку
            # если всё равно смотрит не туда - попробуй 0, 180 или 270
            self.entity = load_furniture('monitor', size, x, z + 0.15, top_y,
                                         rotation_y=90, axis=axis)
            self.screen = None
            return

        # запасной вариант из кубов
        self.stand = Entity(model='cube', scale=(0.1, 0.2, 0.1),
                            position=(x, top_y + 0.1, z + 0.15),
                            color=color.rgba(25, 25, 25))
        self.body = Entity(model='cube', scale=(0.75, 0.5, 0.06),
                           position=(x, top_y + 0.45, z + 0.2),
                           color=color.rgba(15, 15, 15))
        self.screen = Entity(model='cube', scale=(0.68, 0.42, 0.01),
                             position=(x, top_y + 0.45, z + 0.16),
                             color=screen_color, unlit=True)


class Chair:
    """Кресло охранника."""
    def __init__(self, position):
        x, y, z = position
        if has_model('chair'):
            size, axis = FURNITURE_SIZES['chair']
            # 270 - кресло смотрит на стол
            # если всё равно стоит не туда - попробуй 90
            self.entity = load_furniture('chair', size, x, z, -0.5,
                                         rotation_y=270, collider='box', axis=axis)
            # модель пришла без текстуры - красим в тёмный
            self.entity.color = color.rgba(40, 40, 45)
            return

        # запасной вариант из кубов
        self.seat = Entity(model='cube', scale=(0.5, 0.08, 0.5),
                           position=(x, y + 0.45, z),
                           color=color.rgba(30, 30, 35), collider='box')
        self.back = Entity(model='cube', scale=(0.5, 0.6, 0.08),
                           position=(x, y + 0.8, z + 0.25),
                           color=color.rgba(30, 30, 35), collider='box')
        self.base = Entity(model='cube', scale=(0.1, 0.45, 0.1),
                           position=(x, y + 0.22, z),
                           color=color.rgba(20, 20, 20))


# === СОЗДАНИЕ ИГРЫ ===

app = Ursina()
window.fullscreen = True
window.vsync = False
render.setShaderAuto()

# пол с текстурой
floor = Entity(
    model='plane', scale=(12, 1, 10), position=(0, -0.5, 0),
    color=color.white, texture='floor', collider='box',
)
floor.texture_scale = (6, 5)

# стены
wall_back = Entity(model='cube', scale=(12, 4, 0.3), position=(0, 1.5, 5), color=color.gray, collider='box')
wall_front = Entity(model='cube', scale=(12, 4, 0.3), position=(0, 1.5, -5), color=color.gray, collider='box')
wall_left = Entity(model='cube', scale=(0.3, 4, 10), position=(-6, 1.5, 0), color=color.gray, collider='box')
wall_right = Entity(model='cube', scale=(0.3, 4, 10), position=(6, 1.5, 0), color=color.gray, collider='box')

# потолок
ceiling = Entity(
    model='plane', scale=(12, 1, 10), position=(0, 3.5, 0),
    rotation=(180, 0, 0), color=color.dark_gray, double_sided=True,
)

# тусклая потолочная лампа
lamp = Entity(model='cube', scale=(1.5, 0.15, 0.4), position=(0, 3.4, 0), color=color.white, unlit=True)
lamp_spot = SpotLight(position=(0, 3.3, 0), color=color.rgba(200, 190, 160, 255))
lamp_spot._light.setAttenuation(Vec3(1, 0.2, 0.1))
lamp_spot._light.getLens().setFov(90)

# очень тусклый ambient
AmbientLight(color=color.rgba(30, 30, 40, 255))

# холодный свет от мониторов
monitor_glow = PointLight(
    position=(0, 1.2, 3.6),
    color=color.rgba(120, 160, 220, 255),
)
monitor_glow._light.setAttenuation(Vec3(1, 0.3, 0.15))

# === МЕБЕЛЬ ОХРАННИКА ===

desk = Desk((0, -0.5, 4.0))

# три монитора на столешнице, смотрят на игрока
monitor_l = Monitor(-0.85, 4.0, desk.top_y, screen_color=color.rgba(90, 130, 170))
monitor_c = Monitor(0, 4.0, desk.top_y, screen_color=color.rgba(120, 160, 200))
monitor_r = Monitor(0.85, 4.0, desk.top_y, screen_color=color.rgba(90, 130, 170))

# клавиатура
if has_model('keyboard'):
    size, axis = FURNITURE_SIZES['keyboard']
    keyboard = load_furniture('keyboard', size, 0, 3.6, desk.top_y, axis=axis)
else:
    keyboard = Entity(model='cube', scale=(0.5, 0.03, 0.2),
                      position=(0, desk.top_y + 0.02, 3.6),
                      color=color.rgba(25, 25, 25), collider='box')

# кресло за спиной игрока (развернись назад чтобы увидеть)
chair = Chair((0, -0.5, 2.2))

# игрок
player = FirstPersonController(position=(0, 1, 2.8), speed=5)

# фонарик
flashlight = Flashlight()

# UI
battery_bar = Entity(
    parent=camera.ui, model='quad', scale=(0.3, 0.02),
    position=(-0.35, -0.45), color=color.rgba(80, 80, 80, 255),
)
battery_fill = Entity(
    parent=camera.ui, model='quad', scale=(0.3, 0.02),
    position=(-0.35, -0.45), color=color.rgba(100, 200, 100, 255),
)
hint_text = Text(
    parent=camera.ui, text='F - фонарик',
    position=(-0.85, -0.48), scale=1.2,
    color=color.rgba(200, 200, 200, 255),
)


def update():
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


app.run()