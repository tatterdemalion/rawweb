import os
import hashlib
import time
import json

from datetime import datetime
import exifread

from flask import (request, jsonify, render_template, abort, url_for)
from werkzeug import secure_filename

from rawweb import app
from rawweb import db
from rawweb.models import Photo, Photographer
from rawweb.utils import create_directory
from rawweb.tasks import create_web_formats


ALLOWED_EXTENSIONS = set(['NEF', 'SRW'])
OTHER_EXTENSIONS = set(['JPEG', 'JPG'])
ESCAPE_FILES = set(['exports', 'thumbnails', '.DS_Store'])


def get_metadata(stream):
    metadata = exifread.process_file(stream)
    original_date = metadata['EXIF DateTimeOriginal']
    created = datetime.strptime(original_date.values, '%Y:%m:%d %H:%M:%S')
    stream.seek(0)  # make the stream reusable
    metadata.update({'created': created})
    return metadata


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


def save_photo_2_db(path, metadata, created_path, photographer_id=None):
    photo = Photo(id=path,
                  photographer_id=photographer_id,
                  taken_at=metadata['created'],
                  size=os.path.getsize(get_absolute(path)))
    db.session.add(photo)
    db.session.commit()


@app.route("/api/photographer/", methods=['GET', 'POST'])
def api_photographer():
    if request.method == 'GET':
        id_ = request.args.get('id')
        if id_:
            photographer = Photographer.query.get(id_)
            if photographer:
                return jsonify(**{'results': photographer.serialize})
            return jsonify(**{'results': False})
        photographers = Photographer.query.all()
        return jsonify(**{'results': [i.serialize for i in photographers]})

    elif request.method == 'POST':
        name = json.loads(request.data).get('name')
        if name:
            photographer = Photographer(name=name)
            db.session.add(photographer)
            db.session.commit()
            return jsonify(**{'results': True})
        return jsonify(**{'results': False})


@app.route("/api/", methods=['GET', 'PUT', 'DELETE'])
def api():
    upload_to = os.path.abspath(app.config['UPLOAD_FOLDER'])
    path = request.args.get('path', '')
    photographer_id = request.args.get('photographer_id')
    abspath = get_absolute(path)
    if request.method == 'GET':
        if photographer_id != 'NaN':
            photos = Photo.query.filter_by(
                photographer_id=photographer_id).all()
        else:
            photos = Photo.query.all()
        photo_ids = [i.id for i in photos]
        media_host = app.config['MEDIA_HOST']
        paths = []
        for filename in os.listdir(abspath):
            if filename in ESCAPE_FILES:
                continue
            filepath = os.path.join(path, filename)
            fileabspath = get_absolute(filepath)
            pathtype = get_pathtype(fileabspath)
            if pathtype == 'file' and filepath not in photo_ids:
                continue
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
        photographer_id = request.values.get('photographer-id')
        if photographer_id == 'all':
            photographer_id = None
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
                save_photo_2_db(
                    os.path.join(created_path, filename),
                    metadata, created_path, photographer_id)
                create_web_formats.delay(outpath, upload_to, created_path)
                return jsonify(**{'results': True})
        return jsonify(**{'results': False})

    elif request.method == 'DELETE':
        if os.path.isfile(abspath):
            os.remove(abspath)
            os.remove(os.path.join(upload_to, 'exports', get_jpeg_path(path)))
            os.remove(os.path.join(upload_to,
                                   'thumbnails', get_jpeg_path(path)))
        return jsonify(**{'path': path})


@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
