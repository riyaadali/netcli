# netcli
This is a tool I wrote to help network administrators run SSH commands on multiple devices at once and retrieve the output. How it works:

1. Place a list of IPs or hostnames into 'hosts.txt'
2. Place a list of CLI commands into 'commands.txt'
3. Run 'python netcli.py'

The tool will login to each device with the specified credentials, auto-accept the SSH key, then execute the list of commands sequentially. You can specify the delay between commands as well. The tool will take the output from the device and write it into a file named '[HOSTNAME].txt'.

Supports multithreading and also connections via SOCKS5 proxies.
