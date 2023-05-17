
import struct
from typing import NamedTuple

import memory
import pretty
import processes
import win32


class Match(NamedTuple):
	address:int
	value:float|int

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
		print("Search for lesser values.")
		current=memory.scan_memory(self._handle)
		for m in self.snapshot.copy():
			a=m.value
			read_func=[current.read_value_int32,current.read_value_float32][self._type]
			b=read_func(m.address)
			if not b:
				continue
			delta=b-a
			#print(f"Address={m.address} Snapshot={a} Read={b} Delta={delta}")
			self.snapshot.remove(m)
			if delta<0:
				self.snapshot.append(Match(m.address,b))
		if len(self.snapshot)>0:
			self._history.append("-")
		self.print_matches()


	def _cmd_find_value(self,value):
		""" value: any """
		print(f"Search for {['integer','float'][self._type]} {value}.")
		scan_result=memory.scan_memory(self._handle)
		print(f"Scanned size: {pretty.pretty_size(scan_result.size())}.")
		encoding=['i','f'][self._type]
		current_matches=set([x.address for x in self.snapshot])
		new_matches=set(scan_result.search(struct.pack(encoding,value)))
		if len(current_matches)>0:
			intersection=current_matches.intersection(new_matches)
		else:
			intersection=new_matches

		# Only update history when something is found.
		if len(intersection)>0:
			self._history.append(value)

		self.snapshot=[]
		for m in intersection:
			value=scan_result.read_value_int32(m)
			self.snapshot.append(Match(m,value))

		self.print_matches()

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
				for a in self._snapshot_addresses():
					ok=ok and memory.write(data,self._handle,a)
			else:
				address=int(tokens[1])
				ok=ok and memory.write(data,self._handle,address)
			print(("Poke failed!","Poke successful.")[ok])
		except (IndexError,ValueError):
			raise Controller.CommandError

	def _cmd_reset(self,tokens)->None:
		print("Search reset.")
		self._history:list=[]
		self._type:int=-1
		self.snapshot:list[Match]=[]

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

	def _snapshot_addresses(self)->list:
		return [x.address for x in self.snapshot]

	def print_matches(self):
		print(f"History: {self._history}")
		if len(self.snapshot)>0:
			print(f"{len(self.snapshot)} matches.\nAddresses: {pretty.format_big_list([x.address for x in self.snapshot])}")
		else:
			print("No matches.")
		#for x in self.snapshot:
		#	print(x)

def main():
	mem=memory.MemoryBlocks({
			0:b"d\x00\x00\x00\x0C\x00\x00\x00____",
			64:b"abcdefgh\0\0\0\0\1\2\50\0\0\0",
			1000:b"\x00\x00\xc8\x42",# float32 100.0 0x48C80000
			1200:b"\2\0\0\0\2\0\0\0\x0A\0\0\0\x64\0\0\0"
			})

	def mock_find_pid_by_process_name(s):
		return 1000 if s=="test" else -1

	def mock_scan_memory(handle):
		return mem

	def mock_write(data,handle,address):
		ok=mem.write(address,data)
		print(f"Mock write {data} at {address}.")
		for k,v in mem.items():
			print(k," ",v)
		return ok

	processes.find_pid_by_process_name=mock_find_pid_by_process_name
	win32.OpenProcess=lambda *x:1234
	win32.CloseHandle=lambda *x:True
	memory.scan_memory=mock_scan_memory
	memory.write=mock_write

	c=Controller()
	c.run()

if __name__=="__main__":
	main()
