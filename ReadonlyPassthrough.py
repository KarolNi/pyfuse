#!/usr/bin/env python3
""" Read only passthrough file system using nrclark's pyfuse """

# TODO:
# direct_io=True

try:
    from .pyfuse import tools, BasicFs, FileAttributes
except (SystemError, ImportError):
    from pyfuse import tools, BasicFs, FileAttributes
import os
import sys


class ReadonlyPassthrough(BasicFs):

    def __init__(self, base_path):
        self.base_path = base_path
        super(ReadonlyPassthrough, self).__init__()

    def _full_path(self, path):
        if path[0] == '/':
            return os.path.join(self.base_path, path[1:])
        else:
            return os.path.join(self.base_path, path)

    def access(self, path, mask):
        if mask & os.W_OK:  # check if write permission is asked
            return -tools.ERRNO_CONSTANTS["EACCES"]

        if not os.access(self._full_path(path), mask):
            return -tools.ERRNO_CONSTANTS["EACCES"]

        return 0

    def open(self, path, info):
        # check if file is opened for read only
        if (info.flags & 0x03) != tools.FCNTL_CONSTANTS["O_RDONLY"]:
            return -tools.ERRNO_CONSTANTS["EACCES"]

        # TODO check access?
        try:
            info.handle = os.open(self._full_path(path), info.flags)
        except Exception as e:
            print(e)  # TODO
            return -tools.ERRNO_CONSTANTS["ENOENT"]

        return 0

    def readdir(self, path):
        # check if directory exists
        if not os.path.isdir(self._full_path(path)):
            return -1, []

        retval = [".", ".."]
        retval.extend(os.listdir(self._full_path(path)))

        return 0, retval

    def getattr(self, path):
        # check if file/dir exists
        if not os.path.exists(self._full_path(path)):
            return -tools.ERRNO_CONSTANTS["ENOENT"]

        attributes = FileAttributes()
        stats = os.stat(self._full_path(path))
        attributes.size = stats.st_size
        # reset write permission bits
        attributes.mode = stats.st_mode & 0o37777777555
        attributes.uid = stats.st_uid
        attributes.gid = stats.st_gid
        attributes.mtime = int(stats.st_mtime)
        attributes.ctime = int(stats.st_ctime)
        return 0, attributes

    def read(self, path, size, offset, info):
        os.lseek(info.handle, offset, os.SEEK_SET)
        data = os.read(info.handle, size)
        return len(data), data

    def release(self, path, info):
        os.close(info.handle)


def main():
    """ Main routine for launching filesystem. """

    passthrough = ReadonlyPassthrough(sys.argv[1])
    del sys.argv[1]
    sys.exit(passthrough.main(sys.argv, foreground=True))


if __name__ == "__main__":
    main()

