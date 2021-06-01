import sys
from PIL import Image, ImageChops
import random
import os

def intensify(emojiName, sourceImg, scale=1,loops=1,duplicate=1,shift=3):
    is_animated = hasattr(sourceImg, 'is_animated') and sourceImg.is_animated
    frames = 1
    time_scale = float(scale)
    shift_amount = int(shift)
    animation_loops = int(loops)
    if is_animated:
        frames = sourceImg.n_frames
        frame_duration = get_time_per_frame(sourceImg) * time_scale
    else:
        frame_duration = 40 * time_scale
        animation_loops = animation_loops if animation_loops > 2 else 10
    shift_range = range(shift_amount * -1, shift_amount)

    print(frame_duration)
    out_frames = []
    for loop in range(0, animation_loops):
        for frame in range(0, frames):
            sourceImg.seek(frame)
            for d in range(0, int(duplicate)):
                x = random.choice(shift_range)
                y = random.choice(shift_range)
                zoomed = ImageChops.offset(sourceImg, x, y)
                out_frames.append(zoomed)

    out = os.path.splitext(emojiName)[0] + "-intensifies.gif"
    print(out)
    out_frames[-1].save(out, format='GIF', append_images=out_frames[0:-1], save_all=True,
                        duration=frame_duration, transparency=1, loop=0)
    return {'name': out, 'path': out}


def get_time_per_frame(PIL_Image_object):
    """ Returns the average framerate of a PIL Image object """
    PIL_Image_object.seek(0)
    frame_count = duration = 0
    for f in range(0, PIL_Image_object.n_frames):
        try:
            frame_count += 1
            duration +=  PIL_Image_object.info['duration'] if 'duration' in PIL_Image_object.info else 1
            PIL_Image_object.seek(PIL_Image_object.tell() + 1)
        except EOFError:
            try:
                return duration / frame_count
            except:
                return 1
    return 1

