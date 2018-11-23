import paramiko
import datetime
import socks
import re
import sys
import time
import socks
import logging
from threading import Thread, Lock
import Queue


# --- Variables to Customize ---

proxies = ["1.1.1.1"] # Define socks proxies here
useProxy = False # Enable / disable socks proxy

beastmode = True # Enable / disable multithreading
numThreads = 20 # Number of threads

commandDelay = 1 # Time between sending individual lines (seconds)


# --- Globals ---

q = Queue.Queue() # Define the multithreading queue
threadlock = Lock() # Define a multithread lock

failedHosts = list() # List of failed hosts
successHosts =list() # List of successful hosts



# --- Classes ---

class sshshell: # Class defining SSH session for interactive shell

	def __init__(self, address, username, password, proxy=True):
		
		self.paramiko = None # Clear any existing paramiko objects from this new object
		
		self.host = address
		
		self.fulloutput = "" # Variable used for full output of all commands combined
		
		self.connected = False # Connection state for the object, default not connected
		
		self.client = paramiko.SSHClient() # Define the paramiko ssh connection object
		
		self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Auto-accept new SSH keys
		
		self.sockproxy = ""
		
		self.success = False # Only set to true if commands have been sent to device successfully
		
		logging.debug("*** CONNECTING TO HOST %s" % self.host)
		
		if proxy: # If socks proxy option is enabled
		
			for jump in proxies: # For every jump proxy, try to create a socket
				
				try:
				
					logging.info("Connecting to socks proxy %s" % jump)
					
					s = socks.socksocket() # Create a socks-based socket
					
					s.settimeout(2)
					
					s.set_proxy(socks.SOCKS5, addr=jump, port=1080, username=username, password=password) # Proxy connection parameters (assumes common user / pass for everything)
					
					s.connect((self.host, 22))
					
					self.sockproxy = jump
					
					break
					
				except Exception as e:
				
					logging.debug("Error - Cannot connect to host via %s proxy" % jump)
					
					logging.debug(e)
					
					s.close()
					
			
		try: # Now attempt the connection
		
			if proxy:
			
				self.client.connect(hostname=self.host, username=username, password=password, sock=s) # Connect using socket s
				
				logging.info("Connected to host via %s proxy" % self.sockproxy)
				
			else:
				
				self.client.connect(hostname=self.host, username=username, password=password)
				
				logging.info("Connected to host %s directly" % self.host)
				
			self.connected = True
			
			self.shell = self.client.invoke_shell(width=150)
			
		except Exception as e:
		
			#print "[ %s ][ %s ] Job failed." % (timeNow(), '{0: <15}'.format(self.host))
			
			logging.debug("Error - Cannot connect to host.")
			
			logging.debug(e)
			
	
	def sendCommands(self, commands): # Send each command in the 'commands.txt' list
	
		if self.connected == True:
		
			logging.info("Sending commands to host.")
			
			output = self.shell.recv(15000) # Strips the initial stdout info (e.g. the banner or prompt)
			
			self.fulloutput += cleanOutput(output)
			
			for command in commands:
			
				try:
				
					self.shell.send(command)
					
					time.sleep(commandDelay)
					
					output = self.shell.recv(10000000000) # Take everything from the recieved buffer
					
					self.fulloutput += cleanOutput(output) # Append output to fulloutput after cleaning
					
					self.success = True
					
				except Exception as e:
				
					logging.debug("Error: Sending commands to host failed.")
					
					self.success = False
					
					break
					
		else: # If not connected
		
			logging.info("Connection to host not open, cannot send commands.")
			
		
		# If all commands were sent successfully
		
		if self.success:
		
			threadlock.acquire(True) # Acquire lock for printing
			
			print '[ %s ][ %s ] Job completed successfully.' % (timeNow(),'{0: <15}'.format(self.host))
						
			threadlock.release()
			
			logging.info("Job completed successfully")
			
		else:
		
			threadlock.acquire(True) # Acquire lock for printing

			print '[ %s ][ %s ] Job failed.' % (timeNow(),'{0: <15}'.format(self.host))
			
			threadlock.release()
			
			logging.info("Error: Job failed.")
			
		self.client.close()
		
	
	def writeOutput(self, filename): # Function to save stdout to file
		
		if self.fulloutput:
		
			f = open(filename, 'w')
			
			f.write(self.fulloutput)
			
			f.close()
			
			logging.info("Output written to file %s." % filename)
			
	
	def getTimestamp(self): # Function to get the current date
	
		now = datetime.datetime.now()
		
		return str(now.strftime("%Y-%m-%d %H-%M"))
		
	
def readFile(filename, stripnew=False, checkTail=False): # Function to read items from a text file and return in a list

	hosts = list()
	
	try:
	
		with open(filename) as file:
		
			for line in file:
			
				if stripnew:
				
					line = line.strip()
					
				hosts.append(line) # Stores each IP in the 'hosts' list
				
	except:
	
		print "[ %s ][ Error ] Error opening file '%s'. Please check filename." % (timeNow(), filename)
		
		logging.debug("Error - Cannot open file %s" % filename)
		
		sys.exit(0)
		
	if checkTail: # Checks the last command in the list to make sure it has a return string \n at the end, if not add it
	
		if "\n" not in hosts[-1]:
		
			hosts[-1] += "\n"
			
	return hosts


def cleanOutput(output): # Removes all ansi escape characters from a terminal output

	ansi_escape = re.compile(r'\x1B\[[0-?]*[-/]*[@-~]')
	
	return ansi_escape.sub('', output)
	
def timeNow(): # Returns the current date and time

	return str(datetime.datetime.now())

def banner(): # Prints the CLI banner for the program

	print "\n"
	
	print "NetCLI\n"
	
	print "*** Starting Run ***"
	
def footer(failedHosts, successHosts): # Prints a summary at the end of the program

	print "\n -- Execution Summary --"
	
	print "{0: <20}".format("Successful hosts:"), len(successHosts)
	
	print "{0: <20}".format("Failed hosts:"), len(failedHosts)
	
	print "\n"
	
	print " -- List of Failed Hosts --"
	
	for item in failedHosts:
	
		print item
		
	print "\n"
	
def logConfig(): # Configure logging settings

	logging.basicConfig(
		filename="messages.log",
		level=logging.DEBUG,
		format="%(asctime)s:%(levelname)s:%(threadName)s:%(message)s"
		)

def getAuth():

	username = raw_input("Username: ")
	
	password = raw_input("Password: ")
	
	return (username, password)
	
def normalConnect(host, username, password, commands): # Function for normal connections

	connection = sshshell(host, username, password, proxy=useProxy)
	
	if connection.connected == True:
	
		connection.sendCommands(commands)
		
		connection.writeOutput("%s.txt" % (str(connection.host)))
		
		connection.client.close()
		
	if connection.success:
	
		successHosts.append(connection.host)
		
	else:
	
		failedHosts.append(connection.host)
		
		
def worker(username, password, commands):

	while True:
	
		host = q.get()
		
		normalConnect(host,username,password,commands)
		
		q.task_done()
		

def main():

	#Initial program setup
	
	logConfig()
	
	banner()
	
	myhosts = readFile("hosts.txt", stripnew=True) # Loads hosts into list myhosts, strip newline chars
	
	mycommands = readFile("commands.txt", checkTail=True) # Loads commands into list mycommands
	
	creds = getAuth() # set creds tuple manually (['user', 'pass']) for hardcoded username / password
	
	
	# Normal connection
	
	if beastmode == False:
	
		for host in myhosts:
		
			normalConnect(host, creds[0], creds[1], mycommands)
			
	else: # Multithread connection
	
		for i in range(numThreads):
		
			t = Thread(target=worker, args=(creds[0], creds[1], mycommands))
			
			t.setDaemon(True)
			
			t.start()
			
		for host in myhosts: # Load hosts into a queue object
		
			q.put(host)
			
		q.join()
		
	# Final program outputs
	
	footer(failedHosts, successHosts)
	
if __name__ == "__main__":

	main()
	
	
	
		
		
	