import os
import stat
import mimetypes
import pkg_resources

from fp_lib.common import log
from fp_lib import date
from fp_lib import fs
from fp_lib import structure
from fp_lib.system import Disk
from fp_lib.system import OS


FS_CONTROLLER = None


LOG = log.getLogger(__name__)


def get_version():
    try:
        version = pkg_resources.get_distribution('fp.httpfs').version
    except pkg_resources.DistributionNotFound:
        version = 'beta'

    return version


class FSManager(object):

    def __init__(self, home):
        self.home = home
        self.search_history = structure.LastNList(10)

    def get_abs_path(self, path):
        if isinstance(path, str):
            return os.path.join(self.home, path)
        else:
            return os.path.join(self.home, *path)

    def path_exists(self, path):
        return os.path.exists(self.get_abs_path(path))

    def get_path_dict(self, path):
        pathstat = self.stat(path)
        return {'name': os.path.basename(path[-1]),
                'size': self.human(pathstat.st_size),
                'modify_time': date.parse_timestamp2str(
                    pathstat.st_mtime, '%Y/%m/%d %H:%M'),
                'type': 'folder' if stat.S_ISDIR(pathstat.st_mode) else 'file',
                }

    def editable(self, path):
        abs_path = self.get_abs_path(path)
        if os.path.isfile(abs_path):
            t, _ = mimetypes.guess_type(abs_path)
            if t in ['text/plain', 'application/x-sh']:
                return True
        return False

    def mkdir(self, path):
        abs_path = self.get_abs_path(path)
        if self.path_exists(abs_path):
            return FileExistsError(path)
        os.makedirs(abs_path)

    def rename(self, path, new_name):
        abs_path = self.get_abs_path(path)
        new_path = os.path.join(os.path.dirname(abs_path), new_name)
        os.rename(abs_path, new_path)

    def rm(self, path, force=False):
        abs_path = self.get_abs_path(path)
        if not self.path_exists(path):
            raise FileNotFoundError('path not exists: %s' % abs_path)
        LOG.debug('delete dir: %s', path)
        fs.remove(abs_path, recursive=force)

    def listdir(self, path):
        return os.listdir(self.get_abs_path(path))

    def stat(self, path):
        if isinstance(path, str):
            return os.stat()
        else:
            return os.stat(self.get_abs_path(path))

    def access(self, path, *args):
        return os.access(self.get_abs_path(path), *args)

    def ls(self, path, all=False):
        dirs = []
        if self.is_file(path):
            path_dict = self.get_path_dict(path)
            path_dict['editable'] = self.editable(path)
            dirs.append(path_dict)
            return dirs
        for child in self.listdir(path):
            child_path = path[:]
            child_path.append(child)
            if not all and (child.startswith('.') or
                            not self.access(child_path, os.R_OK)):
                continue
            path_dict = self.get_path_dict(child_path)
            path_dict['editable'] = self.editable(child_path)
            dirs.append(path_dict)
        return sorted(dirs, key=lambda k: k['type'], reverse=True)

    def _get_file_type(self, file_name):
        suffix = os.path.splitext(file_name)[1]
        file_suffix_map = {
            'video': ['mp4', 'avi', 'mpeg'],
            'pdf': ['pdf'],
            'word': ['word'],
            'excel': ['xls', 'xlsx'],
            'archive': ['zip', 'tar', 'rar', '7zip'],
            'python': ['py', 'pyc']
        }
        if not suffix:
            return 'file'
        if suffix:
            suffix = suffix[1:].lower()
            for key, values in file_suffix_map.items():
                if suffix in values:
                    return key
            return 'file'

    def human(self, size):
        ONE_KB = 1024
        ONE_MB = ONE_KB * 1024
        ONE_GB = ONE_MB * 1024
        if size >= ONE_GB:
            return '{:.2f} GB'.format(size / ONE_GB)
        elif size >= ONE_MB:
            return '{:.2f} MB'.format(size / ONE_MB)
        elif size >= ONE_KB:
            return '{:.2f} KB'.format(size / ONE_KB)
        else:
            return '{:.2f} B'.format(size)

    def get_file_content(self, path):
        if not self.path_exists(path):
            return FileNotFoundError('path is not exists: %s' % path)
        if not self.is_file(path):
            return ValueError('path is not a file: %s' % path)
        abs_path = self.get_abs_path(path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return ''.join(lines)

    def is_file(self, path):
        abs_path = self.get_abs_path(path)
        return os.path.isfile(abs_path)

    def save(self, path, fo):
        if not fo:
            raise ValueError('file is null')
        save_path_list = path[:]
        save_path_list.extend(os.path.dirname(fo.filename).split('/'))
        save_path = self.get_abs_path(save_path_list)
        file_name = os.path.basename(fo.filename)

        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except FileExistsError:
                pass
        fo.save(os.path.join(save_path, file_name))

    def disk_usage(self):
        return Disk.usage(self.home)

    def _parse_path_to_linux(self, dirPath):
        if OS.is_windows():
            return '/'.join(dirPath.split('\\'))
        else:
            return dirPath

    def _split_path(self, path_string):
        """Parse string path to list
        """
        if OS.is_windows():
            return path_string.split('\\')
        return path_string.split('/')

    def find(self, partern):
        """Find files by partern name
        E.g. *.py, setup.py
        """
        matched_pathes = []
        for dirPath, name in fs.find(self.home, partern):
            path = self._split_path(os.path.join(dirPath, name))
            path_dict = self.get_path_dict(path)
            path_dict['pardir'] = self._parse_path_to_linux(
                dirPath[len(self.home):])
            matched_pathes.append(path_dict)
        if partern not in self.search_history.all():
            self.search_history.append(partern)
        return matched_pathes
