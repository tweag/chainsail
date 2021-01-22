'''
Classes which allow writing out stuff (samples, energies, ...) to
different locations (local file systems, cloud storage, ...)
'''
from abc import abstractmethod, ABCMeta
from pickle import dump, load
from io import BytesIO, StringIO
import os


def sanitize_basename(basename):
    """

    Args:
      basename: 

    Returns:

    """
    return basename if basename[-1] == '/' else basename + '/'


def make_sure_dir_exists(output_path):
    """

    Args:
      output_path: 

    Returns:

    """
    os.makedirs(output_path[:output_path.rfind('/')], exist_ok=True)

    
def pickle_to_stream(data):
    """Pickles a Python object and writes it to a BytesIO stream

    Args:
      data: 

    Returns:

    """
    bytes_stream = BytesIO()
    dump(data, bytes_stream)
    bytes_stream.seek(0)
    return bytes_stream


class AbstractStorage(metaclass=ABCMeta):
    """ """
    @staticmethod
    @abstractmethod
    def _make_data_stream(data):
        """Make a byte stream object.

        Args:
          data(object): object to convert into a byte stream

        Returns:

        """
        pass
    
    @abstractmethod
    def write(self, data, **kwargs):
        """Write data to some kind of permanent storage.

        Args:
          data(object): data to write
          **kwargs: 

        Returns:

        """
        pass


class AbstractFileSystemStorage(AbstractStorage):
    def __init__(self, default_basename, default_mode_flags):
        """Writes something to the file system.

        Args:
          default_basename(str): basename (folder) of location the
            pickled Python object will be written to
          default_mode_flags(str): mode flags to pass to open() call

        Returns:

        """
        self._default_basename = sanitize_basename(default_basename)
        self._default_mode_flags = default_mode_flags


class FileSystemPickleStorage(AbstractFileSystemStorage):
    def __init__(self, default_basename):
        """Pickles a Python object and writes it to the file system.

        Args:
          default_basename(str): basename (folder) of location the
            pickled Python object will be written to

        Returns:

        """
        super().__init__(default_basename, 'wb')

    @staticmethod
    def _make_data_stream(data):
        """

        Args:
          data: 

        Returns:

        """
        return pickle_to_stream(data)

    def _construct_file_path(self, file_name, basename=None):
        """Construct a full file path (possible relative) from a file name and
        a basename.

        Args:
          file_name(str): file name
          basename(str or None, optional): basename (Default value = None)

        Returns:

        """
        basename = basename or self._default_basename
        if basename is None:
            raise ValueError(('Basename not set. Needs to be either given '
                              'a default in __init__() or as an argument to '
                              'write().'))
        basename = sanitize_basename(basename)
        return basename + file_name

    def write(self, data, file_name, basename=None):
        """Pickles a Python object and writes it to a file.

        Args:
          data(object): data
          basename(str, optional): basename (folder) of location the pickled
        Python object will be written to (Default value = None)
          mode_flags(str): mode flags to pass to open() call
          file_name: 

        Returns:

        """
        file_path = self._construct_file_path(file_name, basename)
        make_sure_dir_exists(file_path)
        with open(file_path, self._default_mode_flags) as opf:
            opf.write(self._make_data_stream(data).getbuffer())

    def read(self, path):
        """Unpickle a file.

        Args:
          path(str): file to unpickle

        Returns:

        """
        with open(self._default_basename + path, "rb") as ipf:
            return load(ipf)


class CloudPickleStorage(AbstractStorage):
    def __init__(self, driver, container, default_basename):
        """Writer that pickles objects and writes them to cloud locations via the
            libcloud Storage API.

        Args:
          s: driver: libcloud driver instance

        Returns:

        """
        self._driver = driver
        self._container = container
        self._default_basename = default_basename

    @staticmethod
    def _make_data_stream(data):
        """

        Args:
          data: 

        Returns:

        """
        return pickle_to_stream(data)

    def _construct_object_name(self, file_name, basename=None):
        """Construct a full object name from a file name and
        a basename.

        Args:
          file_name(str): file name
          basename(str or None, optional): basename (Default value = None)

        Returns:

        """
        basename = basename or self._default_basename
        if basename is None:
            basename = ''
        else:
            basename = sanitize_basename(basename)
        return basename + file_name

    def write(self, data, file_name, basename=None):
        """Uploads data to a new "file" in a given container.

        Args:
          s: data: data to upload
          s: file_name: name of new object in the cloud storage
          data: 
          file_name: 
          basename:  (Default value = None)

        Returns:

        """
        byte_data = self._make_data_stream(data)
        object_name = self._construct_object_name(file_name, basename)
        self._driver.upload_object_via_stream(byte_data, self._container,
                                              object_name)


class FileSystemStringStorage(AbstractStorage):
    def __init__(self, default_basename, default_mode_flags='a'):
        """TODO: test / actually use this

            Writes a string to the file system.

        Args:
          default_basename(str): basename (folder) of location the
        pickled Python object will be written to
          mode_flags(str): mode flags to pass to open() call

        Returns:

        """

    @staticmethod
    def _make_data_stream(data):
        """

        Args:
          data: 

        Returns:

        """
        return StringIO(data)

    def write(self, data, output_path, mode_flags):
        """Writes a string to a file.

        Args:
          data(object): data
          output_path(str): output path to write to
          mode_flags(str): mode flags to pass to open()

        Returns:

        """
        file_path = self._construct_file_path(output_path)
        make_sure_dir_exists(file_path)
        with open(output_path, mode_flags) as opf:
            opf.write(self._make_data_stream(data))

    def read(self, path):
        """Reads a string from a file.

        Args:
          path(str): path of the file

        Returns:

        """
        with open(self._basename + path) as ipf:
            return ipf.read()
