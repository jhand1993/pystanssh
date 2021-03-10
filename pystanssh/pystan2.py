""" Legacy PyStan2 ssh functionality.
"""
import json
from pathlib import Path
from io import StringIO
from numpy import ndarray

from .base import BaseConnection


class PyStan2SSH(BaseConnection):
    """ PyStan2 SSH connector class.  Each method opens, then closes, SSH/SFTP connection.
    """
    def __init__(self, host, username, keypath):
        super().__init__(host, username, keypath)

    def upload_sampling_input(
        self, input_data, iterations, nchains, host_path, fname, stan_code_path,
        init=None, close_connection=True, **kwargs
        ):
        """ Uploads a JSON file containing necessary input for running a PyStan2 sampling script.
        Args:
            input_data (Dict): Dictionary with input data for Stan model.
            iterations (int): Number of HMC samples.
            nchains (int): Number of HMC chains.
            host_path (str or pathlib.Path): Remote host path to send input json file.
            fname (str): Uploaded input data file.  Will always be JSON.
            stan_code_path (str or pathlib.Path): Stan code file path.
            init (Dict or List[Dict]): Initial condition dictionary or a list of initial condition
                dictionaries for each chain.  Default is None.
            close_connection (bool): Close connection once complete.  Default is True.
        
        Returns:
            Dict: Stan input dictionary sent to remote host as JSON file.
        """
        input_data_copy = input_data.copy()
        stan_dict = {}

        # Convert numpy arrays to lists:
        for key, value in input_data.items():
            if type(value) is ndarray:
                input_data_copy[key] = value.tolist()
        
        # Construct dictionary to send as JSON StringIO
        stan_dict['input'] = input_data_copy
        stan_dict['iterations'] = iterations
        stan_dict['nchains'] = nchains
        stan_dict['Stan model'] = stan_code_path.name
        stan_dict['stan_kwargs'] = kwargs

        # Upload Stan code file:
        self.upload_file(stan_code_path, host_path)

        # Send JSON file
        self.upload_jsonobj(stan_dict, host_path, fname, close_connection=close_connection)

        return stan_dict
