# pystanssh
 PyStan I/O between servers with ssh

## SSH Key Setup
SSH keys are needed.  To generate via terminal run the following:
> $ ssh-keygen -t rsa

With Mojave, you might need to run this instead:
> $ ssh-keygen -m PEM -t rsa

You will be prompted to give a name.  Note that on macOS, the key files will generate in your current directory unless an explicit path is given.  Go to the location of your new key files (there should be two: <name> and <name>.pub) and copy the key ID to the host server.  In this example, the keys have been generated in the default user SSH directory ~/.ssh/:
> $ ssh-copy-id -i ~/.ssh/mykey username@my_remote_host.org

You will be prompted to give your password.  Note that the public key will be shared, not the private.