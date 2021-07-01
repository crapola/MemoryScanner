import struct

import memory
import pretty
import processes
import win32

class Controller:

	class CommandError(Exception):
		pass

	def __init__(self)->None:
		self._handle=None
		self._commands=[]
		self._commands.append(("help","h",self._cmd_help,"Help"))
		self._commands.append(("poke","p",self._cmd_poke,"Poke <address> <value> or Poke * <value> to poke all matches."))
		self._commands.append(("reset","r",self._cmd_reset,"Restart search"))
		self._cmd_reset(None)
		self._idiot=0

	def __del__(self):
		ok=("Error","OK")[win32.CloseHandle(self._handle)]
		print("Closing handle:",ok)

	def run(self)->None:
		self._get_process_handle()
		if not self._handle:
			return
		self._loop()

	def _cmd_help(self,tokens)->None:
		print("Available commands:")
		for c in self._commands:
			print(f"'{c[0]}' or '{c[1]}' : {c[3]}")
		print("'q' to exit the program.")

	def _cmd_poke(self,tokens)->None:
		try:
			ok=True
			value=int(tokens[2])
			if tokens[1]=="*":
				for m in self._matches:
					ok=ok and memory.write(struct.pack("i",value),self._handle,m)
			else:
				address=int(tokens[1])
				ok=ok and memory.write(struct.pack("i",value),self._handle,address)
			print(("Poke failed!","Poke successful.")[ok])
		except (IndexError,ValueError):
			raise Controller.CommandError

	def _cmd_reset(self,tokens)->None:
		print("Search reset.")
		self._matches=set()
		self._history=[]

	def _get_process_handle(self)->None:
		pid=-1
		while pid==-1:
			print("Enter executable name:")
			user_input=self._input()
			pid=processes.find_pid_by_process_name(user_input)
			if pid==-1:
				print(f"Process '{user_input}' not found.")
			else:
				print(f"Process '{user_input}' has PID {pid}.")
				break
		self._handle=win32.OpenProcess(0x001F0FFF,False,pid)

	def _input(self)->str:
		user_input=input(">")
		if user_input=="q":
			raise KeyboardInterrupt
		return user_input

	def _loop(self)->None:
		user_input=""
		while user_input!="q":
			print("Enter command")
			user_input=input(">")
			try:
				number=int(user_input)
				self._history.append(number)
				print(f"Search for integer {number}.")
				print(f"History: {self._history}")
				result=memory.scan_memory(self._handle)
				print(f"Total size: {pretty.pretty_size(result.size())}.")
				new_matches=set(result.search(struct.pack('i',number)))
				if len(self._matches)==0:
					self._matches=new_matches
				else:
					self._matches=self._matches.intersection(new_matches)
				if len(self._matches)>0:
					print(f"{len(self._matches)} matches.\nAddresses: {pretty.format_big_list(self._matches)}")
				else:
					print("No matches; search reset.")
					self._history=[]
			except ValueError:
				self._idiot=self._idiot+1
				if user_input:
					tokens=user_input.split()
					for c in self._commands:
						if tokens[0].casefold()==c[0] or tokens[0].casefold()==c[1]:
							try:
								c[2](tokens)
							except Controller.CommandError:
								print(c[3])
							self._idiot=0
				if self._idiot>5:
					print("Enter 'help' for help!")
					self._idiot=0

def main():
	def mock_find_pid_by_process_name(s):
		return 1000 if s=="test 123" else -1

	def mock_scan_memory(handle):
		return memory.MemoryBlocks({0:b"d\x00\x00\x00\x0C\x00\x00\x00____",64:b"abcdefghd\0\0\0\0\1\2\50\0\0\0"})

	def mock_write(data,handle,address):
		if address==0:
			return False
		print(f"Mock write {data} at {address}.")
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
