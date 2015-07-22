import os
import hashlib
import time

from datetime import datetime
import exifread
from rawkit.raw import Raw
from wand.image import Image

from flask import Flask, request, jsonify, render_template
from werkzeug import secure_filename

ALLOWED_EXTENSIONS = set(['NEF', 'SRW'])
OTHER_EXTENSIONS = set(['JPEG', 'JPG'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'output/'
app.config['HOST'] = 'http://localhost:5000/'
app.config['MEDIA_HOST'] = 'http://localhost:5001/'


def get_metadata(stream):
    metadata = exifread.process_file(stream)
    original_date = metadata['EXIF DateTimeOriginal']
    created = datetime.strptime(original_date.values, '%Y:%m:%d %H:%M:%S')
    stream.seek(0)  # make the stream reusable
    return {'created': created}


def get_filename(filename, created):
    md5 = hashlib.md5(filename).hexdigest()
    timestamp = int(time.mktime(created.timetuple()))
    ext = os.path.splitext(filename)[1]
    filename = '%s-%s' % (timestamp, md5) + ext
    return filename


def get_outpath(filename, created_path):
    directory = os.path.join(
        app.config['UPLOAD_FOLDER'], created_path)
    path = os.path.join(directory, filename)
    return path


def get_path_by_created(created):
    return os.path.join(str(created.year), str(created.month),
                        str(created.day))


def check_outpath(path):
    return not os.path.exists(path)


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def is_allowed(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].upper() in ALLOWED_EXTENSIONS


def is_other(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].upper() in OTHER_EXTENSIONS


def get_pathtype(abspath):
    if os.path.isdir(abspath):
        return 'directory'
    elif os.path.isfile(abspath):
        return 'file'
    return


def get_filetype(abspath):
    if is_allowed(abspath):
        return 'raw'
    elif is_other(abspath):
        return 'image'
    return


def get_jpeg_path(filepath):
    ext = os.path.splitext(filepath)[1]
    filepath = filepath[:len(filepath) - len(ext)] + '.jpg'
    return filepath


def create_web_formats(path):
    upload_to = app.config['UPLOAD_FOLDER']
    base_filename = os.path.splitext(os.path.basename(path))[0]
    created_path = os.path.dirname(path.split(upload_to)[-1])
    export_path = os.path.join(
        upload_to, 'exports', created_path,
        base_filename + '.jpg')
    raw = Raw(filename=path)
    create_directory(os.path.dirname(export_path))
    raw.save_thumb(export_path)

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


@app.route("/api/", methods=['GET', 'PUT'])
def api():
    upload_to = app.config['UPLOAD_FOLDER']
    if request.method == 'GET':
        path = request.args.get('path', '')
        media_host = app.config['MEDIA_HOST']
        abspath = upload_to
        root = None
        if path:
            abspath = os.path.join(upload_to, path)
            root = os.path.dirname(path)
            if root:
                root = app.config['HOST'] + 'api/?path=' + root
            else:
                root = app.config['HOST'] + 'api/'
        paths = []
        for filename in os.listdir(abspath):
            if filename in ['exports', 'thumbnails']:
                continue
            filepath = os.path.join(path, filename)
            fileabspath = os.path.join(upload_to, filepath)
            pathtype = get_pathtype(fileabspath)
            url = app.config['HOST'] + 'api/?path=' + filepath
            if pathtype:
                meta = {
                    'path': filepath,
                    'pathtype': pathtype,
                    'filename': filename,
                    'url': url
                }
                if pathtype == 'directory':
                    paths.append(meta)
                if pathtype == 'file':
                    filetype = get_filetype(fileabspath)
                    meta['filetype'] = filetype
                    meta['url'] = media_host + filepath
                    if filetype:
                        if filetype == 'raw':
                            meta['compressed_url'] = "%sexports/%s" % (
                                media_host, get_jpeg_path(filepath))
                            meta['thumbnail_url'] = '%sthumbnails/%s' % (
                                media_host, get_jpeg_path(filepath))
                        paths.append(meta)

        return jsonify(**{'results': {'paths': paths, 'root': root}})

    elif request.method == 'PUT':
        image = request.files.get('image')
        if image and is_allowed(image.filename):
            metadata = get_metadata(image.stream)
            created = metadata['created']
            created_path = get_path_by_created(created)
            filename = get_filename(secure_filename(image.filename),
                                    created)
            outpath = get_outpath(filename, created_path)
            if check_outpath(outpath):
                create_directory(os.path.dirname(outpath))
                image.save(outpath)
                create_web_formats(outpath)
                return jsonify(**{'results': True})
        return jsonify(**{'results': False})


@app.route("/")
def index():
    path = request.args.get('path', '')
    media_host = app.config['MEDIA_HOST']
    return render_template('index.html', path=path, media_host=media_host)

if __name__ == "__main__":
    app.run(debug=True)
