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
        self, input_data, num_samples, num_chains, host_path, fname,
        stan_code=None, stan_code_path=None,
        init=None, close_connection=True, save_json_path=None
        ):
        """ Uploads a JSON file containing necessary input for running a PyStan2 sampling script.
        Args:
            input_data (Dict): Dictionary with input data for Stan model.
            num_samples (int): Number of HMC samples.
            num_chains (int): Number of HMC chains.
            host_path (str or pathlib.Path): Remote host path to send input json file.
            fname (str): Uploaded input data file.  Will always be JSON.
            stan_code (str): If provided, stan_code is uploaded as <fname>.stan file to host_path.
                Default is None.
            stan_code_path (str or pathlib.Path): Stan code file path to upload to host_path.
                Default is None
            init (Dict or List[Dict]): Initial condition dictionary or a list of initial condition
                dictionaries for each chain.  Default is None.
            close_connection (bool): Close connection once complete.  Default is True.
            save_json_path (str or pathlib.Path): If provided, the dictionary is dumped in the
                given path.  If no file name is given, then fname is used. Default is None. 
        
        Returns:
            Dict: Stan input dictionary sent to remote host as JSON file.
        """
        # Convert str to Path for host_path:
        host_path = self._pathtype_check(host_path)

        # Convert arrays to lists:
        input_data_copy = self._convert_arrayitems_to_list(input_data)
        stan_dict = {}
        
        # Construct dictionary to send as JSON StringIO
        stan_dict['data'] = input_data_copy
        stan_dict['num_samples'] = num_samples
        stan_dict['num_chains'] = num_chains

        # Handle init input appropriately, converting arrays to lists as needed:
        if type(init) == dict:
            stan_dict['unique_init'] = False
            stan_dict['init'] = self._convert_arrayitems_to_list(init)
        
        elif init is not None:
            init_full_dict = {}
            stan_dict['unique_init'] = True
            for n in range(num_chains):
                init_full_dict[n] = self._convert_arrayitems_to_list(init[n]) 
            
            stan_dict['init'] = init_full_dict

        # Save stan_dict if requested:
        if save_json_path is not None:
            save_json_path = self._pathtype_check(save_json_path)

            if len(save_json_path.suffix):
                with open(save_json_path, 'w') as f:
                    json.dump(stan_dict, f, indent=4)
            
            # Handle no file name in given path:
            else:
                with open(save_json_path / (fname.split('.')[0] + '.json', 'w')) as f:
                    json.dump(stan_dict, f, indent=4)

        # Upload Stan code file if given:
        if stan_code_path is not None:
            stan_dict['Stan_model'] = stan_code_path.name
            self.upload_file(stan_code_path, host_path)
        
        # If stan_code_path is None but stan_code is not, then upload string as file:
        elif stan_code is not None:
            stan_code_io = StringIO(stan_code)
            fname_root = fname.split('.')[0]
            stan_code_fname = f'{fname_root}.stan'
            stan_dict['Stan_model'] = stan_code_fname
            self.send_fileobject(stan_code_io, host_path / stan_code_fname)

        # Send JSON file
        self.upload_jsonobj(stan_dict, host_path, fname, close_connection=close_connection)

        return stan_dict
