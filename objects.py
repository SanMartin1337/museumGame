"""
Игровые объекты: фонарик и мебель охранника.
"""
from ursina import *
import os


# Размеры мебели в метрах: (размер, по чему мерить: 'max' или 'y')
FURNITURE_SIZES = {
    'desk':     (2.6, 'max'),
    'monitor':  (0.65, 'y'),
    'keyboard': (0.55, 'max'),
    'chair':    (1.5, 'y'),    # было 1.3 - чуть больше
    'locker':   (1.8, 'y'),    # высота шкафа
}


def has_model(name):
    """Проверяет, лежит ли модель в models/ или в корне проекта."""
    for folder in ('models', '.'):
        for ext in ('.glb', '.gltf', '.obj', '.bam'):
            if os.path.exists(os.path.join(folder, name + ext)):
                return True
    return False


def load_furniture(name, target_size, x, z, base_y, rotation_y=0, collider=None, axis='max'):
    """
    Грузит модель, автоматически масштабирует и ставит так:
    низ на base_y, центр модели точно в точке (x, z).
    """
    e = Entity(model=name, rotation_y=rotation_y)

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


def nuke_material(e, c):
    """
    Полностью снимает с ноды шейдер, материал и текстуру и красит в цвет.
    Идёт по ВСЕМ внутренностям модели через родной get_children().
    После этого модель рендерится как обычные кубы/стол - светом и цветом.
    """
    e.clearShader()
    e.clearMaterial()
    e.clearTexture()
    e.setColor(c)
    for child in e.get_children():
        nuke_material(child, c)

class Flashlight:
    """Фонарик игрока: конус света на камере, батарейка садится."""
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
    """
    Монитор на столе.
    tilt - доворот экрана к центру (для боковых мониторов).
    """
    def __init__(self, x, z, top_y, tilt=0, screen_color=color.rgba(110, 150, 190)):
        if has_model('monitor'):
            size, axis = FURNITURE_SIZES['monitor']
            self.entity = load_furniture('monitor', size, x, z + 0.15, top_y,
                                         rotation_y=90 + tilt, axis=axis)
            self.screen = None
            return

        # запасной вариант из кубов
        self.stand = Entity(model='cube', scale=(0.1, 0.2, 0.1),
                            position=(x, top_y + 0.1, z + 0.15),
                            color=color.rgba(25, 25, 25))
        self.body = Entity(model='cube', scale=(0.75, 0.5, 0.06),
                           position=(x, top_y + 0.45, z + 0.2),
                           color=color.rgba(15, 15, 15), rotation_y=tilt)
        self.screen = Entity(model='cube', scale=(0.68, 0.42, 0.01),
                             position=(x, top_y + 0.45, z + 0.16),
                             color=screen_color, unlit=True, rotation_y=tilt)



class Message:
    """Всплывающее сообщение внизу экрана."""
    def __init__(self):
        self.text = Text(
            parent=camera.ui, text='', position=(0, -0.35),
            origin=(0, 0), scale=1.5,
            color=color.rgba(230, 230, 230, 255),
        )
        self.text.enabled = False
        self.timer = 0

    def show(self, msg, duration=2.5):
        self.text.text = msg
        self.timer = duration
        self.text.enabled = True

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.text.enabled = False


class Locker:
    """Шкаф-хранилище за креслом."""
    def __init__(self, position, rotation_y=0):
        x, y, z = position
        if has_model('locker'):
            size, axis = FURNITURE_SIZES['locker']
            self.entity = load_furniture('locker', size, x, z, -0.5,
                                         rotation_y=rotation_y, collider='box', axis=axis)
            # если шкаф приедет белым/чёрным как кресло - раскомментируй:
            # nuke_material(self.entity, color.rgba(60, 70, 85))
        else:
            # запасной вариант из куба
            self.entity = Entity(
                model='cube', scale=(0.8, 1.8, 0.5),
                position=(x, 0.4, z),
                color=color.rgba(60, 70, 85), collider='box',
            )

    def player_near(self, player, radius=1.8):
        """True если игрок стоит рядом со шкафом."""
        d = ((self.entity.x - player.x) ** 2 + (self.entity.z - player.z) ** 2) ** 0.5
        return d <= radius


class LockerUI:
    """
    Окно хранилища: сетка пустых слотов по центру экрана.
    Сюда потом будем класть айтемы.
    """
    def __init__(self, rows=3, cols=4):
        self.rows = rows
        self.cols = cols
        self.slots = [None] * (rows * cols)  # сюда позже встанут предметы
        self.open = False
        self.parts = []

        # тёмная панель-подложка (БЕЗ transparency - с ней авто-шейдер белит)
        # z=1 - она ДАЛЬШЕ от камеры, слоты рисуются поверх
        panel = Entity(parent=camera.ui, model='quad', scale=(0.72, 0.56),
                       position=(0, 0, 1), color=color.rgba(18, 18, 24),
                       unlit=True)
        self.parts.append(panel)

        # заголовок (z=-1 - ближе к камере)
        title = Text(parent=camera.ui, text='ХРАНИЛИЩЕ', position=(0, 0.23, -1),
                     origin=(0, 0), scale=1.5, color=color.rgba(230, 230, 230, 255))
        self.parts.append(title)

        # сетка квадратных слотов
        slot_size = 0.13
        gap = 0.02
        grid_w = cols * slot_size + (cols - 1) * gap
        grid_h = rows * slot_size + (rows - 1) * gap
        start_x = -grid_w / 2 + slot_size / 2
        start_y = grid_h / 2 - slot_size / 2 - 0.03

        for r in range(rows):
            for c in range(cols):
                q = Entity(parent=camera.ui, model='quad',
                           scale=(slot_size, slot_size),
                           position=(start_x + c * (slot_size + gap),
                                     start_y - r * (slot_size + gap), -1),
                           color=color.rgba(60, 60, 70, 255), unlit=True)
                self.parts.append(q)

        self.set_visible(False)

    def set_visible(self, value):
        for p in self.parts:
            p.enabled = value

    def open_ui(self):
        self.open = True
        self.set_visible(True)

    def close_ui(self):
        self.open = False
        self.set_visible(False)


class Chair:
    """Кресло охранника."""
    def __init__(self, position):
        x, y, z = position
        if has_model('chair'):
            size, axis = FURNITURE_SIZES['chair']
            self.entity = load_furniture('chair', size, x, z, -0.5,
                                         rotation_y=180, collider='box', axis=axis)
            # сдираем кривой glTF-шейдер до последней ноды
            # и красим в тёмный - будет освещаться лампой как стол
            nuke_material(self.entity, color.rgba(50, 50, 60))
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

# диагностика при импорте
print('--- диагностика моделей ---')
if os.path.exists('models'):
    print('файлы в models/:', os.listdir('models'))
else:
    print('папки models/ нет!')
for name in FURNITURE_SIZES:
    status = 'найдена' if has_model(name) else 'НЕ НАЙДЕНА (соберу из кубов)'
    print(f'{name}: {status}')
print('---------------------------')