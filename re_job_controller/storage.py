'''
Classes which allow writing out stuff (samples, energies, ...) to
different locations (local file systems, cloud storage, ...)
'''
from abc import abstractmethod, ABCMeta
from pickle import dump, load
from io import BytesIO, StringIO
import os


def sanitize_basename(basename):
    return basename if basename[-1] == '/' else basename + '/'


def make_sure_dir_exists(output_path):
    os.makedirs(output_path[:output_path.rfind('/')])

    
def pickle_to_stream(data):
    '''
    Pickles a Python object and writes it to a BytesIO stream
    '''
    bytes_stream = BytesIO()
    dump(data, bytes_stream)
    bytes_stream.seek(0)
    return bytes_stream


class AbstractStorage(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def _make_data_stream(data):
        '''
        Make a byte stream object.

        :param data: object to convert into a byte stream
        :type data: object
        '''
        pass
    
    @abstractmethod
    def write(self, data, **kwargs):
        '''
        Write data to some kind of permanent storage.

        :param data: data to write
        :type data: object
        '''
        pass


class AbstractFileSystemStorage(AbstractStorage):
    def __init__(self, default_basename, default_mode_flags):
        '''
        Writes something to the file system.

        :param default_basename: basename (folder) of location the 
                                 pickled Python object will be written to
        :type default_basename: str
        :param default_mode_flags: mode flags to pass to open() call
        :type default_mode_flags: str
        '''
        self.default_basename = sanitize_basename(default_basename)
        self.default_mode_flags = default_mode_flags


class FileSystemPickleStorage(AbstractFileSystemStorage):
    def __init__(self, default_basename):
        '''
        Pickles a Python object and writes it to the file system.

        :param default_basename: basename (folder) of location the 
                                 pickled Python object will be written to
        :type default_basename: str
        '''
        super().__init__(default_basename, 'wb')

    @staticmethod
    def _make_data_stream(data):
        return pickle_to_stream(data)

    def _construct_file_path(self, file_name, basename=None):
        '''
        Construct a full file path (possible relative) from a file name and
        a basename.

        :param file_name: file name
        :type file_name: str
        :param basename: basename
        :type basename: str or None
        '''
        basename = basename or self.default_basename
        if basename is None:
            raise ValueError(('Basename not set. Needs to be either given '
                              'a default in __init__() or as an argument to '
                              'write().'))
        basename = sanitize_basename(basename)
        return basename + file_name

    def write(self, data, file_name, basename=None):
        '''
        Pickles a Python object and writes it to a file.

        :param data: data
        :type data: object
        :param basename: basename (folder) of location the pickled
                         Python object will be written to
        :type basename: str
        :param mode_flags: mode flags to pass to open() call
        :type mode_flags: str
        '''
        file_path = self._construct_file_path(file_name, basename)
        make_sure_dir_exists(file_path)
        with open(file_path, self.default_mode_flags) as opf:
            opf.write(self._make_data_stream(data).getbuffer())

    def read(self, path):
        with open(path, "rb") as ipf:
            return load(ipf)


class CloudPickleStorage(AbstractStorage):
    def __init__(self, driver, container, default_basename):
        '''
        Writer that pickles objects and writes them to cloud locations via the
        libcloud Storage API.

        :params driver: libcloud driver instance
        :type driver: subclass of :class:`libcloud.storage.base.StorageDriver`
        '''
        self._driver = driver
        self._container = container
        self._default_basename = default_basename

    @staticmethod
    def _make_data_stream(data):
        return pickle_to_stream(data)

    def _construct_object_name(self, file_name, basename=None):
        '''
        Construct a full object name from a file name and
        a basename.

        :param file_name: file name
        :type file_name: str
        :param basename: basename
        :type basename: str or None
        '''
        basename = basename or self._default_basename
        if basename is None:
            basename = ''
        else:
            basename = sanitize_basename(basename)
        return basename + file_name

    def write(self, data, file_name, basename=None):
        '''
        Uploads data to a new "file" in a given container.

        :params data: data to upload
        :type data: object
        :params file_name: name of new object in the cloud storage
        :type file_name: str
        '''
        byte_data = self._make_data_stream(data)
        object_name = self._construct_object_name(file_name, basename)
        self._driver.upload_object_via_stream(byte_data, self._container,
                                              object_name)


class FileSystemStringStorage(AbstractStorage):
    def __init__(self, default_basename, default_mode_flags='a'):
        '''
        TODO: test / actually use this

        Writes a string to the file system.

        :param default_basename: basename (folder) of location the
                                 pickled Python object will be written to
        :type default_basename: str
        :param mode_flags: mode flags to pass to open() call
        :type mode_flags: str
        '''

    @staticmethod
    def _make_data_stream(data):
        return StringIO(data)

    def write(self, data, output_path, mode_flags):
        '''
        Writes a string to a file.

        :param data: data
        :type data: object
        :param output_path: output path to write to
        :type output_path: str
        :param mode_flags: mode flags to pass to open()
        :type mode_flags: str
        '''
        make_sure_dir_exists(output_path)
        with open(output_path, mode_flags) as opf:
            opf.write(self._make_data_stream(data))

    def read(self, path):
        with open(path) as ipf:
            return ipf.read()
