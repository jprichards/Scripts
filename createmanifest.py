#!/usr/bin/env python

# Python approach to creating basic Manifest.plist for MDM InstallApplication
# ./createmanifest.py <pkg-url> <filename>

import os
import sys
import plistlib
import tempfile
from hashlib import md5

chunk_size = 10485760

def get_md5s(filename, chunksize=chunk_size):
    md5s = []
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(chunksize), b''):
            h = md5()
            h.update(chunk)
            md5s.append(h.hexdigest())

    return md5s

def main():
    url = sys.argv[1]
    filename = sys.argv[2]

    filesize = os.path.getsize(filename)
    md5s = get_md5s(filename)

    d = {"items" : [{"assets" : [{
                  "md5s" : md5s,
                  "kind" : "software-package",
                  "md5-size" : chunk_size,
                  "url" : url
                }]}]}

    output_file = tempfile.NamedTemporaryFile()

    try:
        plistlib.writePlist(d, output_file)
        output_file.seek(0)
        print output_file.read()
    finally:
        output_file.close()

if __name__ == '__main__':
    main()
