from PIL import Image, ImageChops, ImageDraw
import json


def approves(name, sourceImg):

    x, y = sourceImg.size
    outerSize = x * .5
    innerSize = x * .45
    additional_offset = (outerSize - innerSize) / 2
    offset = x * .01
    image_offset = int(x * .1)
    sourceImg = ImageChops.offset(sourceImg, -1 * image_offset, image_offset)

    draw = ImageDraw.Draw(sourceImg, "RGBA")
    draw.rectangle((0,0,x,image_offset), fill=(255, 255, 255))
    draw.rectangle((x-image_offset,0,x,y), fill=(255, 255, 255))
    draw.ellipse(((x - outerSize - offset-1), offset-1, (x - offset+1), (offset + outerSize+1)), fill=(255, 255, 255, 64), outline=(255, 255, 255, 100))
    draw.ellipse(((x - outerSize - offset), offset, (x - offset), (offset + outerSize)), fill=(255, 255, 255), outline=(255, 255, 255))
    draw.ellipse(((x - innerSize - offset - additional_offset), offset + additional_offset, (x - offset - additional_offset), (offset + additional_offset + innerSize)), fill=(0, 170, 0), outline=(255, 255, 255))

    draw.polygon((
        (x - innerSize * .8 - offset - additional_offset), (innerSize * .6 + additional_offset),
        (x - innerSize * .8 - offset - additional_offset), (innerSize * .5 + additional_offset),

        (x - innerSize * .6 - additional_offset), (innerSize * .7 + additional_offset),

        (x - innerSize * .3 - additional_offset), (innerSize * .3 + additional_offset),
        (x - innerSize * .2 - additional_offset), (innerSize * .3 + additional_offset),

        (x - innerSize * .58 - additional_offset), (innerSize * .8 + additional_offset),
        (x - innerSize * .61 - additional_offset), (innerSize * .8 + additional_offset),
                  ),
                 fill=(255, 255, 255), outline=(255, 255, 255))
    split = name.split('.')
    sourceImg.save(split[0] + "_approves." + split[1], quality=95)


if __name__ == '__main__':
    approves("bill.jpg", Image.open("bill.jpg"))
