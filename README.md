# pystanssh
 PyStan I/O between servers with ssh

## SSH Key Setup
SSH keys are needed.  To generate via terminal run the following:
> $ ssh-keygen -t rsa

With Mojave, you might need to run this instead:
> $ ssh-keygen -m PEM -t rsa

You will be prompted to give a name.  Note that on macOS, the key files will generate in your current directory unless an explicit path is given.  Go to the location of your new key files (there should be two: <name> and <name>.pub) and copy the key ID to the host server.  In this example, the keys have been generated in the default user SSH directory ~/.ssh/:
> $ ssh-copy-id -i ~/.ssh/mykey username@my_remote_host.org

You should have to give your password.  Note that the public key will be shared, not the private key.

## Installation

Installing through PyPi is preferred:

> $ pip install pystanssh

## Getting Started

pystanssh provides convenient SSH functionality for running PyStan on a remote server.  Try to have a SSH key to streamline the connection process.  PyStan itself has two working version with different functionality: legacy (PyStan2)[https://pystan2.readthedocs.io/en/latest/getting_started.html] and (PyStan)[https://pystan.readthedocs.io/en/latest/getting_started.html], aka PyStan3.  There is a module for each version to handle discrepencies in these two packages. (Stan)[https://mc-stan.org/] itself has tools for Monte Carlo sampling (NUTS or HMC), Bayesian variational inference, or optimization (L-BFGS).  PyStan2 provides wrappers for compiling models along with sampling, inference, and optimization.  At this time, PyStan3 only has wrappers for compiling models and sampling.  Also, PyStan2 is no longer maintained by the Stan group.  

Some details to note:

* Native python pathlib Path objects work fine.
* Numpy is required so to resolve datatype issues when building jsonizable data types.
* Uploaded data for a given Stan model is sent via SFTP as a json file.
* You cannot just upload Stan source as a string.  Don't be that person.

### pystanssh with PyStan v3.0 or greater

Start by importing the unmaintained legacy pystan module from pystanssh:
```python
from pystanssh import pystan
```

Next, you need to instantiate an PyStan2SSH object with the host server name, your username, and the location of your public authentication key file:
```python
from pathlib import Path
host_name = 'random server'
user_name = 'random name'
rsa_key_file = Path('/wherever-your-key-file-is/key-file')
ps = pystan.PyStan2SSH(host_name, user_name, rsa_key_file)
```

A pystanssh workflow provides a convenience method to create and upload a JSON file that contains all necessary data and metadata to instantiate a provided model.  
```python
data = {
    'x': [1, 2, 3, 4],
    'y': [2, 4, 6, 8]
}

# In this workflow, all chains will have the same initial conditions:
init = {
    'a': 2,
    'b': 0
}

num_samples = 1000
num_chains = 4
test_model = 'test.stan'

test_model_path = Path('/some/path/somewhere') / model
host_path = Path('/remote/path')

json = ps.upload_sampling_input(
    data, num_samples, num_chains, host_path, test_model, test_model_path, init=init,
    save_json_path=test_model_path / f'{test_model}.json'
)
```

The PyStanSSH also has convenience methods to upload related shell or python scripts for running PyStan2 on the target remote server.
```python
# Likely need to write some type of shell or slurm command to run a python script (to actually run PyStan) on your remote server or cluster.
# These commands will upload two extra files to your host path:
server_run_script = Path('some_script.sh')
pystan_python_script = Path('some_python_script_to_run_pystan_on_server.py)

ps.upload_file(server_run_script, host_path)
ps.upload_file(pystan_python_script, host_path)
```
The script above uploads a JSON file for model 'test.stan' located at '/some/path/somewhere/' to a host server directory '/remote/path' while saving a local copy of said JSON file to '/some/path/somewhere/test.stan.json'.  It also uploads the stan model file to the same directory.  The 'init' kwarg provides initial conditions for this model's parameters 'a' and 'b'.  Note that this 'init' input can be a single dictionary (which will provide the same initial conditions for reach chain), or a list of dictionaries, with each dictionary corresponding to one chain.

You can provide Stan source code as a block string, but this will be uploaded as a file to the host server instead of being included in the input JSON file.  Note that PyStan 3 will only build with code given as a string, not as a path to the source code file. With PyStan 2, you can provide a file name for our Stan model instead of providing a model code string. 

### pystanssh with PyStan 2

Using pystanssh with legacy PyStan 2 apart from naming convention changes does currently work, but keep in mind that in switching from PyStan 3 to PyStan 2, you'll need to keep in mind the change in keyword arguments (I.e. 'num_samples' -> 'iterations' and 'num_chains' -> 'nchains').  PyStan 3 does have a slightly revised workflow relative to legacy PyStan 2, (so keep that in mind)[https://pystan.readthedocs.io/en/latest/upgrading.html#upgrading].   
