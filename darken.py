from PIL import Image

img = Image.open('textures/ceiling.png').convert('RGB')
# 0.4 = 40% яркости. Хочешь темнее - 0.25, светлее - 0.6
dark = img.point(lambda p: int(p * 0.4))
dark.save('textures/ceiling_dark.png')
print('готово: textures/ceiling_dark.png')