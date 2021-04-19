""" Base logic and class for all PyStan modules
"""
from pathlib import Path
import getpass
from os import system
import json
from io import StringIO
import gzip
from shutil import copyfileobj

from numpy import ndarray, generic
import paramiko

class BaseConnection(object):
    """ Base class for all SSH clients used to move PyStan input/output files
        between local device and remote host with PyStan installation.
    Args:
        host (str): Target remote host address name.
        username (str): Username for login.
        keypath (str): Path to RSA key.
    """
    def __init__(self, host, username, keypath):
        self.host = host
        self.username = username
        # Convert Path instance to string:
        self.keypath = str(keypath)
        try:
            self.key = paramiko.RSAKey.from_private_key_file(self.keypath)
        
        except Exception as e:
            print('Issue loading public key file.')
            print(e)
            self.key = None
        self.stfp_tunnel = None  # stfp connection attribute
        self.client = None # SSH client instance
        self.port = 22
        self.timeout = 1000

    def _change_port(self, new_port):
        """ Change default SSH port value 22 to new_port:
        Args:
            new_port (int): New port number.
        """
        self.port = new_port
    
    def _pathtype_check(self, path_obj):
        """ Internal method to check if path_obj is a pathlib.Path instance.
            If it is a string, then path_obj is converted to pathlib.Path type.
        Args:
            path_obj (str or pathlib.Path): Candidate path object to check type
        
        Returns:
            pathlib.Path: path_obj as pathlib.Path instance
        """
        return Utility.pathtype_check(path_obj)
    
    def _convert_arrayitems_to_list(self, array_dict):
        """ Internal method converting copy of input dictionary's array items to
            lists.
        Args:
            array_dist (Dict): Dictionary to check for items that are type numpy ndarray.
                If so, converts said arrays to lists.
        
        Returns:
            List: Copied dictionary with arrays converted to lists.
        """
        # Convert numpy arrays to lists:
        array_dict_copy = array_dict.copy()
        for key, value in array_dict.items():
            if type(value) is ndarray:
                array_dict_copy[key] = value.tolist()

            # Recursively handle nested dictionaries:
            elif type(value) is dict:
                self._convert_arrayitems_to_list(value)
            
            # Try to convert numpy scalar types to corresponding python native types:
            elif isinstance(value, generic):
                array_dict_copy[key] = value.item()
        
        return array_dict_copy

    def connect_ssh(self):
        """ Connect to host using paramiko.SSHClient()  instance.
        Returns:
            self.client: SSH client instance.
        """
        # Check to see if connection already exists.  If not, create client instance and connect:
        if self.client is None:
            try:
                self.client = paramiko.SSHClient()
                self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.keypath,
                    look_for_keys=True,
                    timeout=self.timeout
                )

            except paramiko.AuthenticationException as e:
                # If authentication doesn't work, try with a password:
                print(f'Check your SSH key for host {self.host}, username {self.username}.')
                try_password = input('Try password?  [y/n]: ')

                if try_password == 'y':
                    try:
                        self.client.connect(
                            self.host,
                            port=self.port,
                            username=self.username,
                            password=getpass.getpass(),
                            timeout=self.timeout
                        )
                    
                    except paramiko.AuthenticationException as e2:
                        print('Wrong password.')
                        raise e2

                # Else, raise authentication exception:
                else:
                    print('Connection failed.')
                    raise e
        else:
            print(f'Connection alrady established for {self.host}')

        return self.client
    
    def connect_sftp(self, host_path=None):
        """ Open sftp connection to host.
        Args:
            host_path (str): Directory to load on host. If None, then no change in directory
                performed. Uses SFTP.chdir() method.  Default is None.
            
        Returns:
            self.sftp: SFTP tunnel instance.
        """
        # Connect if needed:
        if self.client is None:
            self.connect_ssh()
        
        # Open SFTP tunnel:
        self.stfp_tunnel = self.client.open_sftp()

        # Change cwd on host to host_dir if given:
        if host_path:
            try:
                self.stfp_tunnel.chdir(host_path)
            
            except FileNotFoundError as e:
                print(e)
                print(f'Check {host_path} to make sure it exists.')

        return self.stfp_tunnel
    
    def send(self, local_path, host_path):
        """ Send file given by local_path to host_path on host machine using SFTP.
        Args:
            local_path (str or pathlib.Path): Local file path to send up to host.
            host_path (str or pathlib.Path): Host path to recieve sent file.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes: Sent file attribute instance.

        """
        # Open SFTP tunnel if not already open
        if self.stfp_tunnel is None:
            self.connect_sftp()

        # Send file:
        send_output = self.stfp_tunnel.put(str(local_path), str(host_path))

        return send_output
    
    def send_fileobject(self, file_object, host_path):
        """ Send file object to host_path on host machine using SFTP:
        Args:
            file_object (file-like object): File object to send up to host.
            host_path (str or pathlib.Path): Host path to recieve sent file.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes: Sent file attribute instance.
        """
        # Open SFTP tunnel if not already open
        if self.stfp_tunnel is None:
            self.connect_sftp()
        
        # Send file:
        send_output = self.stfp_tunnel.putfo(file_object, str(host_path))

        return send_output

    def get(self, host_path, local_path):
        """ Get file from remote machine from host_path on local machine local_path using SFTP.
        Args:
            host_path (str or pathlib.Path): Host path to recieve sent file.
            local_path (str or pathlib.Path): Local file path to send up to host.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes: Grabbed file attribute instance.

        """
        # Open SFTP tunnel if not already open
        if self.stfp_tunnel is None:
            self.connect_sftp()

        # Send file:
        get_output = self.stfp_tunnel.get(str(host_path), str(local_path))

        return get_output

    def get_fileobject(self, host_path):
        """ Get file from host_path on host machine using SFTP and return file object:
        Args:
            host_path (str or pathlib.Path): Host path to recieve sent file.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes: Grabbed file attribute instance.
        """
        # Open SFTP tunnel if not already open
        if self.stfp_tunnel is None:
            self.connect_sftp()
        
        # Send file:
        get_output = self.stfp_tunnel.getfo(str(host_path), file_object)

        return get_output
    
    def close_sftp(self):
        """ Closes SFTP tunnel instance if open.
        Returns:
            Bool: True is successful.
        """
        if self.stfp_tunnel is None:
            print('No SFTP tunnel open.')

        else:
            self.stfp_tunnel.close()
            self.stfp_tunnel = None
        
        return True
    
    def close_ssh(self):
        """ Closes SSH Client if open.
        Returns:
            Bool: True is successful.
        """
        if self.client is None:
            print('No SSH client connected.')
        
        else:
            # Close SFTP tunnel first:
            if self.stfp_tunnel:
                self.close_sftp()
            
            self.client.close()
            self.client = None
        
        return True

    def upload_obj(self, obj, host_path, fname, close_connection=True):
        """ Uploads file-like object converted to StringIO object to host_path
        Args:
            obj (Dict): File-like object to send to host path.
            host_path (str or pathlib.Path): Path on host to send and save obj.
            fname (str): File name for file saved on host machine.
            close_connection (bool): Close connection once complete.  Default is True.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes
        """
        host_path = self._pathtype_check(host_path)

        # Make sure obj is StringIO type:
        if type(obj) is not StringIO:
            obj = StringIO(obj)
        
        # Handle error with printed message, returning None instead.
        try:
            print(f'Uploading file {fname} to {self.host}...')
            send_output = self.send_fileobject(obj, host_path)
            print('Done.')
        
        except Exception as e:
            print(f'Error occured uploading {fname}.')
            print(e)
            send_output = None

        # Close connection:
        if close_connection:
            self.close_ssh()
    
        return send_output

    def upload_jsonobj(self, dictobj, host_path, fname, close_connection=True):
        """ Upload dictionary-like object to host with path host_path / fname. 
        Args:
            dictobj (Dict): Dictionary-like object that can be converted to JSON string dump.
            host_path (str or pathlib.Path): Path on host to send data.
            fname (str): File name for file saved on host machine.  Will always be a json file.
            close_connection (bool): Close connection once complete.  Default is True.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes
        """
        # Convert to Path object and make sure file name is *.json:
        fname_json = fname.split('.')[0] + '.json'
        host_path = self._pathtype_check(host_path)
        
        host_json_path = host_path / fname_json

        # Make JSON string dump and send to host path:
        try:
            dict_dumps = json.dumps(dictobj, indent=4)
        
        # Let user know they have nonserializable data types (probably from numpy) in 
        # dictionaries:
        except TypeError as e:
            print('Check non-array/non-list data types in input or init dictionaries!')
            print('All data types must be native python types.')
            raise(e)
    
        return self.upload_obj(
            dict_dumps, host_json_path, fname_json, close_connection=close_connection
            )

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
            raise
            send_output = None
        
        # Close connection:
        if close_connection:
            self.close_ssh()

        return send_output

    def download_file(self, host_path, file_path, close_connection=True, compress=True):
        """ Upload file to host server location host_path.
        Args:
            host_path (str or pathlib.Path): Host location to copy file to.
            file_path (str or pathlib.Path): Local file location.
            close_connection (bool): Close connection once complete.  Default is True.
            compress (bool): If True, then the file is downloaded and then compressed.
                Default is True.
        
        Returns:
            paramiko.sftp_attr.SFTPAttributes
        """
        # Check to make sure given paths are pathlib.Path instances:
        host_path = self._pathtype_check(host_path)
        file_path = self._pathtype_check(file_path)
        
        # Check to see if file name with suffix given in host_path:
        if not file_path.suffix:
            # Otherwise, grab it from file_path stem:
            fname = host_path.name
            file_path = file_path / fname
        
        else:
            fname = file_path.name
        
        # Try uploading file to host:
        try:
            print(f'Downloading file {fname} from {self.host}...')
            get_output = self.get(host_path, file_path)
            print('Done.')
        
        except Exception as e:
            print(f'Error occured downloading file {fname}.')
            raise
            get_output = None
        
        # Close connection:
        if close_connection:
            self.close_ssh()

        if compress:
            Utility.compress_file(file_path)

        return get_output
    
    def run_command(self, cmd, cmd_path):
        """ Wrapper for 'exec_command' method to run a single command on a ssh
            terminal at the given path.
        Args:
            cmd (str): Command to execute on remote terminal.
            cmd_path (str or pathlib.Path): Path to execute command.
        """
        if self.client is None:
            self.connect_ssh()
        
        try:
            print(f'Running command \'{cmd}\'...')
            full_command = f'cd {str(cmd_path)};{cmd}'
            exec_out = self.client.exec_command(full_command)
            print('Done.')
        
        except:
            raise

        return str(exec_out[1].read(), encoding='utf-8')


class KeyUploader(object):
    """ Container class for retreiving and uploading key to a host machine.
    """
    @staticmethod
    def get_private_key(keypath):
        """ Method for retrieving local RSA key
        Args:
            keypath (str): Local location of private key file.
        
        Returns:
            str: Private RSA key.
        """
        try:
            # Snag RSA key from path given:
            rsa_key = paramiko.RSAkey.from_private_key_file(keypath)
        
        except paramiko.SSHException as e:
            print(f'Check given path {keypath}.')
            raise e

        return rsa_key
    
    @staticmethod
    def upload_private_key(keypath, host, username):
        """ Upload private RSA key located at keypath to given host for user username.
        Args:
            keypath (str): Local location of private key file.
            host (str): Host name.
            username (str): Username
        """
        try:
            system(f'ssh-copy-id -i {keypath} {user}@{host}>/dev/null 2>&1')
            system(f'ssh-copy-id -i {keypath}.pub {user}@{host}>/dev/null 2>&1')
        
        except FileNotFoundError as e:
            print(f'Check given path {keypath}.')
            raise e
        
        except:
            raise

class Utility(object):
    """ Container class for misc functionality
    """
    @staticmethod
    def compress_file(path, drop_original=True):
        """ Compresses file given by path using gzip.
        Args:
            path (str or pathlib.Path): Path of file to compress.
            drop_original (bool): If True, then the original file is dropped.
                Default is True.
        """
        path = Utility.pathtype_check(path)
        fname = path.name
        gzip_path = path.parent / f'{fname}.gz'
        with open(path, 'rb') as f_in:
            with gzip.open(gzip_path, 'wb') as f_out:
                copyfileobj(f_in, f_out)
        
        # Drop original file if requested:
        if drop_original:
            path.unlink()

    @staticmethod
    def pathtype_check(path_obj):
        """ Method to check if path_obj is a pathlib.Path instance.
            If it is a string, then path_obj is converted to pathlib.Path type.
        Args:
            path_obj (str or pathlib.Path): Candidate path object to check type
        
        Returns:
            pathlib.Path: path_obj as pathlib.Path instance
        """
        if type(path_obj) is str:
            return Path(path_obj)
        
        else:
            return path_obj