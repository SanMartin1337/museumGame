from ursina import *

app = Ursina()

# ничего больше в сцене нет - только один тёмный квадрат в UI
panel = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.72, 0.56),
    color=color.rgba(18, 18, 24),
    unlit=True,
)

print('цвет панели прямо перед стартом:', panel.color)

app.run()