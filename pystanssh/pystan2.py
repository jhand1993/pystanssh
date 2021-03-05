""" Legacy PyStan2 ssh functionality.
"""
import json
from pathlib import Path
from io import StringIO

from .base import BaseConnection


class PyStan2SSH(BaseConnection):
    """ PyStan2 SSH connector class.  Each method opens, then closes SSH/SFTP connection.
    """
    def __init__(self, host, username, keypath):
        super().__init__(host, username, keypath)
    
    def upload_data(self, data, host_path, fname):
        """ Upload data as a file-like object to host with path host_path / fname.
        Args:
            data (Dict): Dictionary of input data for PyStan model run.
            host_path (str or pathlib.Path): Path on host to send data.
            fname (str): File name for file saved on host machine.  Will always be a json file.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes
        """
        # Convert to Path object and make sure file name is *.json:
        fname_json = fname.split('.')[0] + '.json'
        if type(host_path) is str:
            host_path = Path(host_path)
        
        host_file_path = host_path / fname_json

        # Make JSON string dump and send to host path:
        data_dumps = json.dumps(data, indent=4)
        
        # Handle error with printed message, returning None instead.
        try:
            print(f'Uploading {fname_json} to {self.host}...')
            send_output = self.send_fileobject(StringIO(data_dumps), host_file_path)
            print('Done.')
        
        except Exception as e:
            print(f'Error occured uploading {fname_json}.')
            print(e)
            send_output = None

        # Close connection.
        self.close_ssh()
    
        return send_output

    def upload_file(self, file_path, host_path):
        """ Upload file to host server location host_path.
        Args:
            file_path (str or pathlib.Path): Local file location.
            host_path (str or pathlib.Path): Host location to copy file to.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes
        """
        # Check to make sure given paths are pathlib.Path instances:
        if type(host_path) is str:
            host_path = Path(host_path)

        if type(file_path) is str:
            file_path = Path(file_path)
        
        # Check to see if file name with suffix given in host_path:
        if not host_path.suffix:
            # Otherwise, grab it from file_path stem:
            fname = file_path.name
            host_path = host_path / fname
        
        else:
            fname = host_path.name
        
        # Try uploading file to host:
        try:
            print(f'Uploading file {fname} to {self.host}...')
            send_output = self.send(file_path, host_path)
            print('Done.')
        
        except Exception as e:
            print(f'Error occured uploading file {fname}.')
            print(e)
            send_output = None
        
        # Close connection:
        self.close_ssh()

        return send_output

