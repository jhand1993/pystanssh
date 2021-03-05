""" Base logic and class for all PyStan modules
"""
from pathlib import Path
import getpass
from os import system

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
        self.keypath = keypath
        self.key = paramiko.RSAKey.from_private_key_file(self.keypath)
        # self.password = getpass.getpass()
        # self.connection = None  # ssh connection attribute
        self.stfp_tunnel = None  # stfp connection attribute
        self.client = None # SSH client instance
        self.port = 22

    def _change_port(self, new_port):
        """ Change default SSH port value 22 to new_port:
        Args:
            new_port (int): New port number.
        """
        self.port = new_port
    
    def connect_ssh(self):
        """ Connect to host using paramiko.SSHClient()  instance.
        Returns:
            self.client: SSH client isntance.
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
                    timeout=5000
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
                            timeout=5000
                        )
                    
                    except:
                        raise

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
            host_path (str): Directory to load on host. If None, then no change in directory performed.
                Uses SFTP.chdir() method.  Default is None.
            
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
        
        # Treat given paths as strings:
        if type(local_path) is not str:
            local_path = str(local_path)
        
        if type(host_path) is not str:
            host_path = str(host_path)
        
        # Send file:
        send_output = self.stfp_tunnel.put(local_path, host_path)

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
        
        # Treat given paths as strings:
        if type(host_path) is not str:
            host_path = str(host_path)
        
        # Send file:
        send_output = self.stfp_tunnel.putfo(file_object, host_path)

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
        
        # Treat given paths as strings:
        if type(local_path) is not str:
            local_path = str(local_path)
        
        if type(host_path) is not str:
            host_path = str(host_path)
        
        # Send file:
        get_output = self.stfp_tunnel.get(local_path, host_path)

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
        
        # Treat given paths as strings:
        if type(host_path) is not str:
            host_path = str(host_path)
        
        # Send file:
        get_output = self.stfp_tunnel.getfo(file_object, host_path)

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

    



    