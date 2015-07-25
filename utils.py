import os

from rawkit.raw import Raw
from wand.image import Image


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_web_formats(path, upload_to):
    base_filename = os.path.splitext(os.path.basename(path))[0]
    created_path = os.path.dirname(path.split(upload_to)[-1])
    export_path = os.path.join(
        upload_to, 'exports', created_path,
        base_filename + '.jpg')
    if os.path.exists(export_path):
        return
    raw = Raw(filename=path)
    create_directory(os.path.dirname(export_path))
    try:
        raw.save_thumb(export_path)
    except:
        return
    # create thumbnails
    thumbnail_path = os.path.join(
        upload_to, 'thumbnails', created_path,
        base_filename + '.jpg')
    create_directory(os.path.dirname(thumbnail_path))
    with Image(filename=export_path) as img:
        width = img.size[0]
        height = img.size[1]
        w = 500
        h = int(height * (float(w) / width))
        with img.clone() as i:
            i.sample(w, h)
            i.save(filename=thumbnail_path)
