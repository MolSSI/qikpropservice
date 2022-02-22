import hashlib

# TODO: hash the options as well


hash_method = hashlib.sha1


# Taken from https://flask.palletsprojects.com/en/2.0.x/patterns/requestchecksum/
class ChecksumCalcStream(object):

    def __init__(self, stream):
        self._stream = stream
        self._hash = hash_method()

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
    checksum = hash_method(file.read()).hexdigest()
    file.seek(0)  # Reset the file seek to the start
    return checksum


def write_file_and_checksum_from_stream(datastream, filepath="streamed.file", chunk_size=4096):
    """Write a file to disk and processes its hash on the fly, best used with a temporary directory"""
    cumulative_hash = hash_method()
    with open(filepath, "wb") as file:
        while True:
            chunk = datastream.read(chunk_size)
            if len(chunk) == 0:
                break
            cumulative_hash.update(chunk)
            file.write(chunk)
    return cumulative_hash.hexdigest()
