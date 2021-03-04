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
        self.connection = None  # ssh connection attribute
        self.stfp = None  # stfp connection attribute
        self.client = None # SSH client instance
        self.port = 22

    def _change_port(self, new_port):
        """ Change default SSH port value 22 to new_port:
        Args:
            new_port (int): New port number.
        """
        self.port = new_port
    
    def connect(self):
        """ Connects to host using paramiko.SSHClient() instance.
        Returns:
            self.client: SSH client isntance.
        """
        # Check to see if connection already exists.  If not, create client instance and connect:
        if self.connection is None:
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

        return self.client
    
    def sftp(self, host_dir=None):
        """ Open sftp connection to host.
        Args:
            Host_dir (str): Directory to load on host. If None, then no change in directory performed.
                Uses SFTP.chdir() method.  Default is None.
            
        Returns:
            self.sftp: SFTP tunnel instance.
        """
        # Connect if needed:
        if self.connection is None:
            self.connect()
        
        # Open SFTP tunnel:
        self.sftp = client.open_sftp()

        # Change cwd on host to host_dir if given:
        if host_dir:
            try:
                sftp.chdir(host_dir)
            
            except FileNotFoundError as e:
                print(f'Check your given directory to make sure it exists.')
                print(e)
        
        return self.stfp
                


class KeyUploader(object):
    """ Container class for retreiving and uploading key to a host machine.
    """
    @staticmethod
    def get_private_key(keypath):
        """ Method for retrieving local RSA key
        Args:
            keypath (str): Local location of private key file.
        
        Returns:
            str: Private RSA key except with SSHException.  Then False.
        """
        try:
            # Snag RSA key from path given:
            rsa_key = paramiko.RSAkey.from_private_key_file(keypath)
        
        except paramiko.SSHException as e:
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

    



    