'''
Classes which allow writing out stuff (samples, energies, ...) to
different locations (local file systems, cloud storage, ...)
'''
from abc import abstractmethod, ABCMeta
from pickle import dump, load
from io import BytesIO, StringIO
import os


def sanitize_basename(basename):
    '''Sanitize a basename.

    Currently only makes sure that the basename ends with a '/'.
    
    Args:
      basename: a basename (like '/some/base/name/' or '/some/base/name')

    Returns:
      str: sanitized basename (ends with '/')
    '''
    return basename if basename[-1] == '/' else basename + '/'


def make_sure_basename_exists(file_path):
    '''Makes sure the basename of a file path exists.

    TODO: log warning if it does.
    
    Args:
      file_path: a (possibly relative) file path
    '''
    os.makedirs(file_path[:file_path.rfind('/')], exist_ok=True)


def pickle_to_stream(obj):
    '''Pickles a Python object and writes it to a BytesIO stream.

    Args:
      obj(object): some pickleable Python object

    Returns:
      BytesIO: byte stream with pickled object
    '''
    bytes_stream = BytesIO()
    dump(obj, bytes_stream)
    bytes_stream.seek(0)
    return bytes_stream


class AbstractStorage(metaclass=ABCMeta):
    @abstractmethod
    def write(self, data, **kwargs):
        '''Write data to some kind of permanent storage.

        Args:
          data(object): data to write
          **kwargs: 

        Returns:

        '''
        pass


class AbstractFileSystemStorage(AbstractStorage):
    def __init__(self, default_basename, default_mode_flags):
        '''Writes something to the file system.

        Args:
          default_basename(str): basename (folder) of location the
            pickled Python object will be written to
          default_mode_flags(str): mode flags to pass to open() call

        Returns:

        '''
        self._default_basename = sanitize_basename(default_basename)
        self._default_mode_flags = default_mode_flags


class FileSystemPickleStorage(AbstractFileSystemStorage):
    def __init__(self, default_basename):
        '''Pickles a Python object and writes it to the file system.

        Args:
          default_basename(str): basename (folder) of location the
            pickled Python object will be written to

        Returns:

        '''
        super().__init__(default_basename, 'wb')

    @staticmethod
    def _make_data_stream(obj):
        '''Takes a Python object and pickles it to a byte stream.
        
        Args:
          obj: Python object to be pickled

        Returns:
          BytesIO: byte stream with pickled object
        '''
        return pickle_to_stream(obj)

    def write(self, data, file_path, basename=None):
        '''Pickles a Python object and writes it to a file.

        Args:
          data(object): data
          file_path: path of file to write data to
          basename(str, optional): basename (folder) of location the pickled
              Python object will be written to (Default value = None)
        '''
        if basename:
            basename = sanitize_basename(basename)
        else:
            basename = self._default_basename
        file_path = basename + file_path
        make_sure_basename_exists(file_path)
        with open(file_path, self._default_mode_flags) as opf:
            opf.write(self._make_data_stream(data).getbuffer())

    def read(self, path):
        '''Unpickle a file.

        Args:
          path(str): file to unpickle

        Returns:
          object: unpickled Python object
        '''
        with open(self._default_basename + path, "rb") as ipf:
            return load(ipf)


class CloudPickleStorage(AbstractStorage):
    def __init__(self, driver, container, default_basename):
        '''Writer that pickles objects and writes them to cloud locations via the
            libcloud Storage API.

        Args:
          driver: libcloud driver instance
          container: libcloud container
          default_basename(str): default basename, usually a simulation path
        '''
        self._driver = driver
        self._container = container
        self._default_basename = default_basename

    @staticmethod
    def _make_data_stream(obj):
        '''Takes a Python object and pickles it to a byte stream.

        Args:
          obj: Python object to be pickled

        Returns:
          BytesIO: byte stream with pickled object
        '''
        return pickle_to_stream(obj)

    def write(self, data, object_name, basename=None):
        '''Uploads data to a new "file" in a given container.

        Args:
          data: data to upload
          object_name(str): name of new object in the cloud storage
          basename(str): basename if other than default (Default value = None)
        '''
        byte_data = StringIO(data)
        if basename:
            basename = sanitize_basename(basename)
        else:
            basename = self._default_basename
        object_name = basename + object_name
        self._driver.upload_object_via_stream(byte_data, self._container,
                                              object_name)


class FileSystemStringStorage(AbstractStorage):
    def __init__(self, default_basename, default_mode_flags='a'):
        '''TODO: test / actually use this

            Writes a string to the file system.

        Args:
          default_basename(str): basename (folder) of location the
        pickled Python object will be written to
          mode_flags(str): mode flags to pass to open() call

        Returns:

        '''
        self._default_basename = default_basename
        self._default_mode_flags = default_mode_flags

    def write(self, data, file_path, basename=None, mode_flags=None):
        '''Writes a string to a file.

        Args:
          data(object): data
          file_path(str): file path to write to
          mode_flags(str): mode flags to pass to open()

        Returns:

        '''
        mode_flags = mode_flags or self._default_mode_flags
        basename = sanitize_basename(basename) or self._default_basename
        file_path = basename + file_path
        make_sure_basename_exists(file_path)
        with open(file_path, mode_flags) as opf:
            opf.write(data)

    def read(self, path):
        '''Reads a string from a file.

        Args:
          path(str): path of the file

        Returns:
          str: string read from file
        '''
        with open(self._default_basename + path) as ipf:
            return ipf.read()
