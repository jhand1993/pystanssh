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
    
    def upload_data(self, data, host_path, fname, close_connection=True):
        """ Upload data as a file-like object to host with path host_path / fname.
        Args:
            data (Dict): Dictionary of input data for PyStan model run.
            host_path (str or pathlib.Path): Path on host to send data.
            fname (str): File name for file saved on host machine.  Will always be a json file.
            close_connection (bool): Close connection once complete.  Default is True.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes
        """
        # Convert to Path object and make sure file name is *.json:
        fname_json = fname.split('.')[0] + '.json'
        host_path = self._pathtype_check(host_path)
        
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

        # Close connection:
        if close_connection:
            self.close_ssh()
    
        return send_output

    def upload_file(self, file_path, host_path, close_connection=True):
        """ Upload file to host server location host_path.
        Args:
            file_path (str or pathlib.Path): Local file location.
            host_path (str or pathlib.Path): Host location to copy file to.
            close_connection (bool): Close connection once complete.  Default is True.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes
        """
        # Check to make sure given paths are pathlib.Path instances:
        host_path = self._pathtype_check(host_path)
        file_path = self._pathtype_check(file_path)
        
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
        if close_connection:
            self.close_ssh()

        return send_output
    
    def run_python_script(
        self, python_path, cmd_opt=None, py_args=None, local_path=None, python_cmd='python'
        ):
        """ Runs a python script on remote host, copying said script to remote location
            if a local path is given.
        
        Args:
            python_path (str or pathlib.Path): Remote host path to run python script.
            cmd_opt (str): String appended between python_cmd and python file name in command.
                Default is None.
            py_args (Tuple): Arguments passed into python script when executed. Default is None.
            local_path (str or pathlib.Path): If provided, the local python file path is copied
                to the given python_path parent directory and then run.  Default is None.
            python_cmd (str): Terminal command to run python file.  Default is 'python'.
        
        Results:

        """
        # set strings to Paths:
        python_path = self._pathtype_check(python_path)

        if local_path is not None:
            local_path = self._pathtype_check(local_path)

            # Add local python file name:
            if not python_path.suffix:
                python_path = python_path / local_path.name
            
            # Make sure local path file name used:
            elif python_path.name != local_path.name:
                python_path = python_path.parent / local_path.name

            self.upload_file(local_path, python_path, close_connection=False)
            self.close_sftp()

        else:
            self.connect_ssh()        

        command_list = [python_cmd]
        # Run python script:
        if cmd_opt is not None:
            command_list.append(cmd_opt)
        
        command_list.append(python_path.name)
        # Handle no args given.
        if py_args is not None:
            py_args_join = ' '.join(py_args)
            command_list.append(py_args_join)

        command = ' '.join(command_list)

        try:
            print(f'Running command on {self.host}...')
            print(command)
            stdin, stdout, stderr = self.client.exec_command(command)
        
        except:
            raise

        # self.close_ssh()
        return stdin, stdout, stderr


