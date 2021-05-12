from PIL import Image, ImageChops, ImageDraw
import json

def approves(filename):
    sourceImg = Image.open(filename)
    draw = ImageDraw.Draw(sourceImg)
    x, y = sourceImg.size
    outerSize = x * .35
    innerSize = x * .33
    additional_offset = (outerSize - innerSize) / 2
    offset = x * .01
    draw.ellipse(((x - outerSize - offset), offset, (x - offset), (offset + outerSize)), fill=(255, 255, 255), outline=(255, 255, 255))
    draw.ellipse(((x - innerSize - offset - additional_offset), offset + additional_offset, (x - offset - additional_offset), (offset + additional_offset + innerSize)), fill=(0, 100, 0), outline=(255, 255, 255))

    draw.polygon((
        (x - innerSize * .8 - offset), (innerSize * .6),
        (x - innerSize * .8 - offset), (innerSize * .5),

        (x - innerSize * .6), (innerSize * .7),

        (x - innerSize * .3), (innerSize * .3),
        (x - innerSize * .2), (innerSize * .3),

        (x - innerSize * .55), (innerSize * .8),
        (x - innerSize * .60), (innerSize * .8),
                  ),
                 fill=(255, 255, 255), outline=(255, 255, 255))
    split = filename.split('.')
    sourceImg.save(split[0] + "_approves." + split[1], quality=95)


if __name__ == '__main__':
    approves("bill.jpg")
    approves("jazmin.jpg")
