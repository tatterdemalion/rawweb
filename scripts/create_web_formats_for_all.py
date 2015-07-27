import os
from api import create_web_formats, app

upload_to = app.config['UPLOAD_FOLDER']

counter = 0

for root, dirs, files in os.walk(upload_to):
    for filename in files:
        ext = os.path.splitext(filename)[1]
        if ext in ['.NEF', '.SRW']:
            create_web_formats(os.path.join(root, filename))
            counter += 1
            if counter % 100 == 0:
                print('%s/? completed' % counter)
