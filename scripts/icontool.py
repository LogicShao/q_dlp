import os

import cairosvg
from PIL import Image


def test():
    import cairocffi as cairo

    # 创建一个简单的 Cairo Surface 测试
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
    context = cairo.Context(surface)

    # 绘制一个矩形
    context.rectangle(10, 10, 80, 80)
    context.set_source_rgb(0, 0, 1)  # 蓝色
    context.fill()

    print("✅ Cairo 库安装成功，绘图测试通过！")


def convert_svg_to_ico(svg_path, ico_path=None, sizes=None):
    # 将 SVG 转成 PNG
    if sizes is None:
        sizes = [(256, 256)]
    if ico_path is None:
        ico_path = svg_path.replace(".svg", ".ico")

    png_path = svg_path.replace(".svg", ".png")
    cairosvg.svg2png(url=svg_path, write_to=png_path)

    # 使用 Pillow 将 PNG 转换为 ICO
    img = Image.open(png_path)
    img.save(ico_path, format='ICO', sizes=sizes)

    # 清理中间文件
    os.remove(png_path)
    print(f"✅ 成功生成图标: {ico_path}")


if __name__ == "__main__":
    svg_path = "icon/run.svg"
    convert_svg_to_ico(
        svg_path, sizes=[
            (16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
