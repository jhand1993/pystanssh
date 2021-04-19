""" Legacy PyStan2 ssh functionality.
"""
import json
from io import StringIO

from .base import BaseConnection


class PyStanSSH(BaseConnection):
    """ PyStan SSH connector class.  Each method opens, then closes, SSH/SFTP connection.
    """
    def __init__(self, host, username, keypath):
        super().__init__(host, username, keypath)

    def upload_sampling_input(
        self, input_data, num_samples, nchains, host_path, fname, stan_code_path,
        init=None, close_connection=True, save_json_path=None
        ):
        """ Uploads a JSON file containing necessary input for running a PyStan2 sampling script.
        Args:
            input_data (Dict): Dictionary with input data for Stan model.
            num_samples (int): Number of HMC samples.
            num_chains (int): Number of HMC chains.
            host_path (str or pathlib.Path): Remote host path to send input json file.
            fname (str): Uploaded input data file.  Will always be JSON.
            stan_code_path (str or pathlib.Path): Stan code file path.
            init (Dict or List[Dict]): Initial condition dictionary or a list of initial condition
                dictionaries for each chain.  Default is None.
            close_connection (bool): Close connection once complete.  Default is True.
            save_json_path (str or pathlib.Path): If provided, the dictionary is dumped in the
                given path.  If no file name is given, then fname is used. Default is None
        
        Returns:
            Dict: Stan input dictionary sent to remote host as JSON file.
        """
        # Convert arrays to lists:
        input_data_copy = self._convert_arrayitems_to_list(input_data)
        stan_dict = {}
        
        # Construct dictionary to send as JSON StringIO
        stan_dict['input'] = input_data_copy
        stan_dict['num_samples'] = num_samples
        stan_dict['num_chains'] = num_chains
        stan_dict['Stan_model'] = stan_code_path.name

        # Handle init input appropriately, converting arrays to lists as needed:
        if type(init) == dict:
            stan_dict['unique_init'] = False
            stan_dict['init'] = self._convert_arrayitems_to_list(init)
        
        else:
            init_full_dict = {}
            stan_dict['unique_init'] = True
            for n in range(nchains):
                init_full_dict[n] = self._convert_arrayitems_to_list(init[n]) 
            
            stan_dict['init'] = init_full_dict

        # Save stan_dict if requested:
        if type(save_json_path) is not None:
            save_json_path = self._pathtype_check(save_json_path)

            if len(save_json_path.suffix):
                with open(save_json_path, 'w') as f:
                    json.dump(stan_dict, f, indent=4)
            
            # Handle no file name in given path:
            else:
                with open(save_json_path / (fname.split('.')[0] + '.json', 'w')) as f:
                    json.dump(stan_dict, f, indent=4)

        # Upload Stan code file:
        self.upload_file(stan_code_path, host_path)

        # Send JSON file
        self.upload_jsonobj(stan_dict, host_path, fname, close_connection=close_connection)

        return stan_dict
