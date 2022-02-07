import hashlib


# Taken from https://flask.palletsprojects.com/en/2.0.x/patterns/requestchecksum/
class ChecksumCalcStream(object):

    def __init__(self, stream):
        self._stream = stream
        self._hash = hashlib.sha1()

    def read(self, bytes):
        rv = self._stream.read(bytes)
        self._hash.update(rv)
        return rv

    def readline(self, size_hint):
        rv = self._stream.readline(size_hint)
        self._hash.update(rv)
        return rv


def generate_checksum_request(request):
    env = request.environ
    stream = ChecksumCalcStream(env['wsgi.input'])
    env['wsgi.input'] = stream
    return stream._hash


def generate_checksum_file(file):
    checksum = hashlib.sha1(file.read()).hexdigest()
    file.seek(0)  # Reset the file seek to the start
    return checksum
