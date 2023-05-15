
import struct

import memory
import pretty
import processes
import win32


class Controller:

	# Search types.
	INT32=0
	FLOAT32=1

	class CommandError(Exception):
		pass

	def __init__(self)->None:
		self._handle=None
		self._commands=[]
		self._commands.append(("help","h",self._cmd_help,"Help"))
		self._commands.append(("poke","p",self._cmd_poke,"Poke <address> <value> or Poke * <value> to poke all matches."))
		self._commands.append(("reset","r",self._cmd_reset,"Restart search."))
		self._commands.append(("greater","+",self._cmd_find_greater,"Find greater values."))
		self._commands.append(("lesser","-",self._cmd_find_lesser,"Find lesser values."))
		self._cmd_reset(None)

		self._type:int=-1
		self.snapshot=None

	def __del__(self):
		ok=("Error","OK")[win32.CloseHandle(self._handle)]
		print("Closing handle:",ok)

	def run(self)->None:
		try:
			self._get_process_handle()
			if not self._handle:
				return
			self._loop()
		except KeyboardInterrupt:
			pass

	def _cmd_find_greater(self,args)->None:
		pass

	def _cmd_find_lesser(self,args)->None:
		print("Find lesser...",args)
		current=memory.scan_memory(self._handle)

		if self.snapshot:
			for m in self._matches.copy(): # Copy to avoid 'RuntimeError: Set changed size during iteration'
				print(m)
				a=self.snapshot.read_value_int32(m)
				b=current.read_value_int32(m)
				delta=b-a
				if delta>=0:
					self._matches.remove(m)
			self.print_matches()
		#	memory.difference_int32(self.snapshot,current)
		# 	for k,v in self.result.items():
		# 		#print(k,v)
		# 		for i,data,other_data in enumerate(zip(v,current[k])):
		# 			#print(i,data,other_data)
		# 			if other_data<data:
		# 				print(i,data,other_data)
		# 				self._matches.add(k+i)
		else:
			print("Error...")
		self.snapshot=current

	def _cmd_find_value(self,value):
		""" value: any """
		self._history.append(value)
		print(f"Search for {['integer','float'][self._type]} {value}.")
		print(f"History: {self._history}")
		result=memory.scan_memory(self._handle)
		print(f"Total size: {pretty.pretty_size(result.size())}.")
		encoding=['i','f'][self._type]
		new_matches=set(result.search(struct.pack(encoding,value)))
		if len(self._matches)==0:
			self._matches=new_matches
		else:
			self._matches=self._matches.intersection(new_matches)
		self.print_matches()
		self.snapshot=result

	def _cmd_help(self,tokens)->None:
		print("Available commands:")
		for c in self._commands:
			print(f"'{c[0]}' or '{c[1]}' : {c[3]}")
		print("'q' to exit the program.")

	def _cmd_poke(self,tokens)->None:
		try:
			ok=True
			value:str=tokens[2]
			pack_type=""
			# Convert user input to bytes.
			try:
				value=int(value)
				pack_type="i"
			except ValueError:
				try:
					value=float(value)
					pack_type="f"
				except ValueError:
					raise Controller.CommandError
			data:bytes=struct.pack(pack_type,value)
			# Write at address.
			if tokens[1]=="*":
				pass
				for m in self._matches:
					ok=ok and memory.write(data,self._handle,m)
			else:
				address=int(tokens[1])
				ok=ok and memory.write(data,self._handle,address)
			print(("Poke failed!","Poke successful.")[ok])
		except (IndexError,ValueError):
			raise Controller.CommandError

	def _cmd_reset(self,tokens)->None:
		print("Search reset.")
		self._matches=set()
		self._history=[]

	def _get_process_handle(self)->None:
		while self._handle==None:
			print("Enter executable name, PID, or nothing to list processes:")
			# Get input.
			user_input:str=self._input()
			if user_input:
				if user_input.isdigit():
					pid=int(user_input)
				else:
					pid=processes.find_pid_by_process_name(user_input)
					if pid==-1:
						print(f"Process '{user_input}' not found.")
					else:
						print(f"Process '{user_input}' has PID {pid}.")
				self._handle=win32.OpenProcess(0x001F0FFF,False,pid)
				if not self._handle:
					print(f"Invalid PID: {pid}.")
					self._handle=None
			else:
				# List processes if entered nothing.
				processes.print_processes()


	def _input(self)->str:
		user_input=input(">")
		if user_input=="q":
			raise KeyboardInterrupt
		return user_input

	def _loop(self)->None:
		user_input=""
		while user_input!="q":
			print("Enter command")
			try:
				user_input=self._input()
				if user_input.isdigit():
					# Has only digit, so we treat as int32.
					self._type=Controller.INT32
					self._cmd_find_value(int(user_input))
				elif user_input.replace(".","",1).isdigit():
					# Is float32.
					self._type=Controller.FLOAT32
					self._cmd_find_value(float(user_input))
				else:
					if user_input:
						tokens=user_input.split()
						for c in self._commands:
							if tokens[0].casefold()==c[0] or tokens[0].casefold()==c[1]:
								try:
									c[2](tokens)
								except Controller.CommandError:
									print(c[3])
			except ValueError:
				pass

	def print_matches(self):
		if len(self._matches)>0:
			print(f"{len(self._matches)} matches.\nAddresses: {pretty.format_big_list(self._matches)}")
		else:
			print("No matches.")

def main():
	mem=memory.MemoryBlocks({
			0:b"d\x00\x00\x00\x0C\x00\x00\x00____",
			64:b"abcdefghd\0\0\0\0\1\2\50\0\0\0",
			1000:b"\x00\x00\xc8\x42",# float32 100.0 0x48C80000
			1200:b"\2\0\0\0\2\0\0\0\x0A\0\0\0\x64\0\0\0"
			})

	def mock_find_pid_by_process_name(s):
		return 1000 if s=="test" else -1

	def mock_scan_memory(handle):
		return mem

	def mock_write(data,handle,address):
		mem.write(address,data)
		print(f"Mock write {data} at {address}.")
		for k,v in mem.items():
			print(k," ",v)
		return True

	processes.find_pid_by_process_name=mock_find_pid_by_process_name
	win32.OpenProcess=lambda *x:1234
	win32.CloseHandle=lambda *x:True
	memory.scan_memory=mock_scan_memory
	memory.write=mock_write

	c=Controller()
	c.run()

if __name__=="__main__":
	main()
