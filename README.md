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

### pystanssh with PyStan2

Start by importing the pystan2 module from pystanssh:
```python
from pystanssh import pystan2
```

Next, you need to instantiate an PyStan2SSH object with the host server name, your username, and the location of your public authentication key file:
```python
from pathlib import Path
host_name = 'random server'
user_name = 'random name'
rsa_key_file = Path('/wherever-your-key-file-is/key-file')
ps2 = pystan2.PyStan2SSH(host_name, user_name, rsa_key_file)
```

PyStan2 model objects require a Stan model source code, while sampling from this object requires a dictionary providing the input data, the number of chains, and the number of iterations.  When sampling a posterior, once frequently specifies the initial conditions of each chain, although this is not necessary.
