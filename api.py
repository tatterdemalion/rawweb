import os
import hashlib
import time

from datetime import datetime
import exifread

from flask import (Flask, request, jsonify, render_template, abort, url_for)
from werkzeug import secure_filename

from utils import create_directory
import tasks


ALLOWED_EXTENSIONS = set(['NEF', 'SRW'])
OTHER_EXTENSIONS = set(['JPEG', 'JPG'])
ESCAPE_FILES = set(['exports', 'thumbnails', '.DS_Store'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'output/'
app.config['HOST'] = 'http://localhost:5000/'
app.config['MEDIA_HOST'] = 'http://localhost:5001/'
app.config.from_envvar('RAWWEB_SETTINGS')


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


def get_jpeg_path(filepath):
    ext = os.path.splitext(filepath)[1]
    filepath = filepath[:len(filepath) - len(ext)] + '.jpg'
    return filepath


def get_root(path):
    if path:
        root = app.config['HOST'] + 'api/'
        if os.path.dirname(path):
            return root + '?path=' + os.path.dirname(root)
        return root
    return


def get_media_url(path):
    return app.config['MEDIA_HOST'] + path


def get_absolute(path):
    absmedia = os.path.abspath(app.config['UPLOAD_FOLDER'])
    if not path:
        return absmedia
    if path and path[0] not in ['/', '..']:
        return os.path.join(absmedia, path)
    abort(403)


@app.route("/api/", methods=['GET', 'PUT'])
def api():
    upload_to = app.config['UPLOAD_FOLDER']
    if request.method == 'GET':
        path = request.args.get('path', '')
        media_host = app.config['MEDIA_HOST']
        paths = []
        abspath = get_absolute(path)
        for filename in os.listdir(abspath):
            if filename in ESCAPE_FILES:
                continue
            filepath = os.path.join(path, filename)
            fileabspath = get_absolute(filepath)
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
                if pathtype == 'file' and is_allowed(filepath):
                    meta['url'] = get_media_url(filepath)
                    meta['compressed_url'] = "%sexports/%s" % (
                        media_host, get_jpeg_path(filepath))
                    absthumb = os.path.join(
                        upload_to, 'thumbnails', get_jpeg_path(filepath))
                    if os.path.exists(absthumb):
                        meta['thumbnail_url'] = '%sthumbnails/%s' % (
                            media_host, get_jpeg_path(filepath))
                    else:
                        meta['thumbnail_url'] = url_for(
                            'static', filename='images/processing.png')
                    paths.append(meta)

        return jsonify(
            **{'results': {'paths': paths, 'root': get_root(path)}})

    elif request.method == 'PUT':
        image = request.files.get('image')
        if image and is_allowed(image.filename):
            metadata = get_metadata(image.stream)
            created = metadata['created']
            created_path = get_path_by_created(created)
            filename = get_filename(secure_filename(image.filename),
                                    created)
            outpath = get_outpath(filename, created_path)
            create_directory(os.path.dirname(outpath))
            if not os.path.exists(outpath):
                image.save(outpath)
                tasks.create_web_formats.delay(outpath, upload_to)
                return jsonify(**{'results': True})
        return jsonify(**{'results': False})


@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
