import argparse
import os

from PIL import Image, ImageOps


def invert_image(image_path, overwrite=False):
    if not os.path.isfile(image_path):
        print(f"❌ 文件不存在: {image_path}")
        return

    try:
        img = Image.open(image_path)

        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb_image = Image.merge("RGB", (r, g, b))
            inverted = ImageOps.invert(rgb_image)
            inverted = Image.merge("RGBA", (*inverted.split(), a))
        elif img.mode in ['RGB', 'L']:
            inverted = ImageOps.invert(img)
        else:
            img = img.convert('RGB')
            inverted = ImageOps.invert(img)

        if overwrite:
            inverted.save(image_path)
            print(f"✅ 覆盖保存: {image_path}")
        else:
            base, ext = os.path.splitext(image_path)
            new_path = f"{base}_inverted{ext}"
            inverted.save(new_path)
            print(f"✅ 新文件已保存: {new_path}")

    except Exception as e:
        print(f"⚠️ 错误: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="反转图片颜色")
    parser.add_argument("image_path", help="输入图片路径")
    parser.add_argument("-o", "--overwrite", action="store_true", help="是否覆盖原图")

    args = parser.parse_args()
    invert_image(args.image_path, args.overwrite)
