"""
Игровые объекты: фонарик и мебель охранника.
"""
from ursina import *
from panda3d.core import MaterialAttrib
import os


def rgba255(r, g, b, a=255):
    """
    В установленной версии Ursina (8.3.0) встроенный color.rgba() больше не делит
    автоматически значения 0-255 на 255 - значения просто обрезаются
    видеокартой до 1.0, что даёт белый цвет вместо задуманного.
    Используй эту функцию вместо color.rgba(), передавая как раньше 0-255.
    """
    return color.rgba(r / 255, g / 255, b / 255, a / 255)


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


def restore_original_colors(e, fallback=rgba255(140, 140, 140, 255)):
    """
    Как nuke_material, но красит КАЖДУЮ часть модели в ЕЁ РЕАЛЬНЫЙ исходный
    цвет из glTF-материала (baseColorFactor), а не в один цвет на всю модель.
    Нужно именно для моделей без картинки-текстуры (только плоский цвет
    в материале) - у таких Panda3D иногда рисует белую заглушку.
    """
    for node_path in e.find_all_matches('**/+GeomNode'):
        node_path.clear_shader()
        node_path.clear_texture()
        geom_node = node_path.node()
        for i in range(geom_node.get_num_geoms()):
            state = geom_node.get_geom_state(i)
            mat_attrib = state.get_attrib(MaterialAttrib)
            if mat_attrib and mat_attrib.get_material() and mat_attrib.get_material().has_base_color():
                c = mat_attrib.get_material().get_base_color()
            else:
                c = fallback
            node_path.set_color(c)

class Flashlight:
    """Фонарик игрока: конус света на камере, батарейка садится.
    Пока не поднят из шкафа - включить нельзя."""
    def __init__(self):
        self.on = False
        self.available = False  # пока False - лежит в шкафу, не в руках у игрока
        self.battery = 100.0
        self.max_battery = 100.0
        self.drain_rate = 2.0

        self.light = SpotLight(
            parent=camera,
            position=(0, -0.3, 0),
            color=rgba255(255, 245, 220, 255),
            rotation=(90, 0, 0),
        )
        self.light._light.setAttenuation(Vec3(1, 0.15, 0.08))
        self.light._light.getLens().setFov(60)
        self.light.enabled = False

    def pickup(self):
        self.available = True

    def toggle(self):
        if not self.available:
            return
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
                          color=rgba255(70, 50, 35), collider='box')
        self.leg_l = Entity(model='cube', scale=(0.08, 0.72, 0.9),
                            position=(x - 1.2, y + 0.36, z),
                            color=rgba255(40, 40, 40), collider='box')
        self.leg_r = Entity(model='cube', scale=(0.08, 0.72, 0.9),
                            position=(x + 1.2, y + 0.36, z),
                            color=rgba255(40, 40, 40), collider='box')
        self.top_y = y + 0.76


class Monitor:
    """
    Монитор на столе.
    tilt - доворот экрана к центру (для боковых мониторов).
    """
    def __init__(self, x, z, top_y, tilt=0, screen_color=rgba255(110, 150, 190)):
        if has_model('monitor'):
            size, axis = FURNITURE_SIZES['monitor']
            self.entity = load_furniture('monitor', size, x, z + 0.15, top_y,
                                         rotation_y=90 + tilt, axis=axis)
            self.screen = None
            return

        # запасной вариант из кубов
        self.stand = Entity(model='cube', scale=(0.1, 0.2, 0.1),
                            position=(x, top_y + 0.1, z + 0.15),
                            color=rgba255(25, 25, 25))
        self.body = Entity(model='cube', scale=(0.75, 0.5, 0.06),
                           position=(x, top_y + 0.45, z + 0.2),
                           color=rgba255(15, 15, 15), rotation_y=tilt)
        self.screen = Entity(model='cube', scale=(0.68, 0.42, 0.01),
                             position=(x, top_y + 0.45, z + 0.16),
                             color=screen_color, unlit=True, rotation_y=tilt)



class Message:
    """Всплывающее сообщение внизу экрана."""
    def __init__(self):
        self.text = Text(
            parent=camera.ui, text='', position=(0, -0.35),
            origin=(0, 0), scale=1.5,
            color=rgba255(230, 230, 230, 255),
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
            restore_original_colors(self.entity)
        else:
            # запасной вариант из куба
            self.entity = Entity(
                model='cube', scale=(0.8, 1.8, 0.5),
                position=(x, 0.4, z),
                color=rgba255(60, 70, 85), collider='box',
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
                       position=(0, 0, 1), color=rgba255(18, 18, 24),
                       unlit=True)
        self.parts.append(panel)

        # заголовок (z=-1 - ближе к камере)
        title = Text(parent=camera.ui, text='ХРАНИЛИЩЕ', position=(0, 0.23, -1),
                     origin=(0, 0), scale=1.5, color=rgba255(230, 230, 230, 255))
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
                           color=rgba255(60, 60, 70, 255), unlit=True)
                self.parts.append(q)

        # предмет "фонарик" лежит в первом слоте (в глубине шкафа) -
        # рисуется ПОВЕРХ обычного пустого слота (z чуть ближе к камере)
        # и кликабелен - у него есть collider, а Ursina сама зовёт on_click
        self.item_taken_callback = None  # main.py подставит сюда функцию
        self.flashlight_taken = False
        self.flashlight_slot = Entity(
            parent=camera.ui, model='quad', scale=(slot_size, slot_size),
            position=(start_x, start_y, -1.001),
            color=rgba255(95, 80, 35, 255), unlit=True, collider='box',
        )
        self.flashlight_label = Text(
            parent=camera.ui, text='🔦', position=(start_x - 0.02, start_y - 0.03, -1.002),
            origin=(0, 0), scale=2.2, color=rgba255(255, 235, 190, 255),
        )
        self.flashlight_slot.on_click = self.take_flashlight
        self.parts.append(self.flashlight_slot)
        self.parts.append(self.flashlight_label)

        self.set_visible(False)

    def take_flashlight(self):
        if self.flashlight_taken:
            return
        self.flashlight_taken = True
        self.flashlight_slot.color = rgba255(35, 35, 40, 255)
        self.flashlight_label.text = ''
        if self.item_taken_callback:
            self.item_taken_callback()

    def set_visible(self, value):
        for p in self.parts:
            p.enabled = value

    def open_ui(self):
        self.open = True
        self.set_visible(True)
        mouse.locked = False
        mouse.visible = True

    def close_ui(self):
        self.open = False
        self.set_visible(False)
        mouse.locked = True
        mouse.visible = False


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
            nuke_material(self.entity, rgba255(50, 50, 60))
            return

        # запасной вариант из кубов
        self.seat = Entity(model='cube', scale=(0.5, 0.08, 0.5),
                           position=(x, y + 0.45, z),
                           color=rgba255(30, 30, 35), collider='box')
        self.back = Entity(model='cube', scale=(0.5, 0.6, 0.08),
                           position=(x, y + 0.8, z + 0.25),
                           color=rgba255(30, 30, 35), collider='box')
        self.base = Entity(model='cube', scale=(0.1, 0.45, 0.1),
                           position=(x, y + 0.22, z),
                           color=rgba255(20, 20, 20))

class Hotbar(Entity):
    """
    Полоска ячеек внизу экрана (как в Minecraft), переключается цифрами 1-5.
    У каждой ячейки два наложенных квадрата: побольше - рамка, поменьше
    сверху - фон. Так получается аккуратная обводка без текстур/картинок.
    """
    SLOT_COUNT = 5

    def __init__(self):
        super().__init__(parent=camera.ui)
        self.selected = 0
        self.items = [None] * self.SLOT_COUNT  # пока пустые слоты - заполним предметами позже

        slot_size = 0.09
        gap = 0.014
        total_width = self.SLOT_COUNT * slot_size + (self.SLOT_COUNT - 1) * gap
        start_x = -total_width / 2 + slot_size / 2
        y = -0.46

        self.slot_borders = []
        self.slot_bgs = []
        self.slot_labels = []

        for i in range(self.SLOT_COUNT):
            x = start_x + i * (slot_size + gap)

            border = Entity(parent=self, model='quad', scale=slot_size * 1.12,
                            position=(x, y, 0), color=rgba255(120, 100, 70, 255), unlit=True)
            bg = Entity(parent=self, model='quad', scale=slot_size,
                       position=(x, y, -0.001), color=rgba255(20, 18, 22, 235), unlit=True)
            number = Text(parent=self, text=str(i + 1), position=(x - 0.017, y - 0.05),
                         scale=0.9, color=rgba255(180, 170, 150, 255))

            self.slot_borders.append(border)
            self.slot_bgs.append(bg)
            self.slot_labels.append(number)

        self.refresh_selection()

    def refresh_selection(self):
        """Подсвечивает выбранную ячейку тёплым золотистым цветом и увеличивает рамку."""
        for i, border in enumerate(self.slot_borders):
            if i == self.selected:
                border.color = rgba255(230, 190, 90, 255)
                border.scale = 0.09 * 1.22
            else:
                border.color = rgba255(120, 100, 70, 255)
                border.scale = 0.09 * 1.12

    def select(self, index):
        if 0 <= index < self.SLOT_COUNT:
            self.selected = index
            self.refresh_selection()


class Inventory(Entity):
    """
    Полноэкранная панель инвентаря, открывается/закрывается по TAB.
    Стилизована под кожаный чемоданчик (тёплые коричневые тона) -
    целиком из примитивов Ursina, без скачанных текстур.
    """
    ROWS = 4
    COLS = 5

    def __init__(self):
        super().__init__(parent=camera.ui, enabled=False)
        self.open = False

        # внешняя "обложка чемодана" - тёмно-коричневая рамка
        self.case_border = Entity(parent=self, model='quad', scale=(0.98, 0.74),
                                  color=rgba255(45, 30, 20, 255), unlit=True)
        # внутренняя панель - светлее, "подкладка"
        self.case_inner = Entity(parent=self, model='quad', scale=(0.94, 0.68),
                                 position=(0, 0, -0.001),
                                 color=rgba255(70, 50, 35, 255), unlit=True)

        self.title = Text(parent=self, text='ИНВЕНТАРЬ', position=(-0.09, 0.32, -0.002),
                          scale=1.6, color=rgba255(225, 200, 160, 255))

        self.slots = []
        slot_size = 0.1
        gap_x = 0.018
        gap_y = 0.022
        grid_w = self.COLS * slot_size + (self.COLS - 1) * gap_x
        grid_h = self.ROWS * slot_size + (self.ROWS - 1) * gap_y
        start_x = -grid_w / 2 + slot_size / 2
        start_y = grid_h / 2 - slot_size / 2 - 0.04

        for row in range(self.ROWS):
            for col in range(self.COLS):
                x = start_x + col * (slot_size + gap_x)
                y = start_y - row * (slot_size + gap_y)
                border = Entity(parent=self, model='quad', scale=slot_size * 1.08,
                                position=(x, y, -0.002), color=rgba255(30, 20, 14, 255), unlit=True)
                bg = Entity(parent=self, model='quad', scale=slot_size,
                           position=(x, y, -0.003), color=rgba255(90, 75, 60, 255), unlit=True)
                self.slots.append(bg)

    def toggle(self):
        self.open = not self.open
        self.enabled = self.open
        mouse.locked = not self.open  # чтобы можно было двигать мышью по инвентарю, а не крутить камеру


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