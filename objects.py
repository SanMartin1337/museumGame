"""
Игровые объекты: фонарик и мебель охранника.
"""
from ursina import *
import os


# Размеры мебели в метрах: (размер, по чему мерить: 'max' или 'y')
FURNITURE_SIZES = {
    'desk':     (2.6, 'max'),   # длина парты
    'monitor':  (0.65, 'y'),    # высота монитора
    'keyboard': (0.55, 'max'),  # длина клавиатуры (было 0.4 - мелко)
    'chair':    (1.3, 'y'),     # высота кресла (было 1.1 - мало)
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


def force_color(e, c):
    e.setMaterialOff(1)
    e.setTextureOff(1)
    e.setLightOff(1)
    e.setColor(c, 1)
    e.setColorScale((0.2, 0.2, 0.22, 1), 1)  # вот эта строка

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


class Chair:
    """Кресло охранника."""
    def __init__(self, position):
        x, y, z = position
        if has_model('chair'):
            size, axis = FURNITURE_SIZES['chair']
            # 180 - кресло лицом к столу
            self.entity = load_furniture('chair', size, x, z, -0.5,
                                         rotation_y=180, collider='box', axis=axis)
            # принудительно красим в тёмный
            force_color(self.entity, color.rgba(45, 45, 50))
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