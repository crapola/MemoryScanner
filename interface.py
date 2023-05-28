import struct
from typing import Any, TypeAlias, cast

import scanner
import system


def number_type(string:str)->type[float]|type[int]|type[str]:
	""" Return number type or str if not a number. """
	try:
		_=int(string)
		return int
	except ValueError:
		try:
			_=float(string)
			return float
		except ValueError:
			return str

class Interface:

	TokenList:TypeAlias=list[float|int|str]

	class Command:
		""" Base class for commands. """
		alias:tuple[str,...]=('',)
		arguments:str=""
		description:str=""
		def __init__(self,interface:'Interface')->None:
			self.interface=interface
		def do(self,tokens:'Interface.TokenList')->bool:
			return True
		def _validate_arguments(self,tokens:'Interface.TokenList',types:list[type])->bool:
			if len(types)>len(tokens):
				print(f"Missing argument(s): {self.arguments}")
				return False
			for token,expected_type in zip(tokens,types):
				if not issubclass(type(token),expected_type):
					print(f"Invalid argument: {token}.")
					return False
			return True

	class Close(Command):
		alias:tuple[str,...]=('close',)
		description:str="Close current process and go back to selection."
		def do(self,_:'Interface.TokenList')->bool:
			if not self.interface.handle:
				return True
			close_ok=system.process_close(self.interface.handle)
			if close_ok:
				self.interface.handle=None
				self.interface.scanner=scanner.Scanner()
			else:
				print("Failed to close handle!")
			return close_ok

	class FindEqual(Command):
		alias:tuple[str,...]=("eq","=")
		arguments:str="<value>"
		description:str="Search for exact value." # TODO: also unchanged values.
		def do(self,tokens:'Interface.TokenList')->bool:
			if not self._validate_arguments(tokens,[float|int]):
				return False
			if not self.interface.scanner.is_started():
				# User didn't start, so do it now with value type and try again.
				self.interface.commands_dict["start"].do([type(tokens[0]).__name__])
				self.interface.commands_dict["eq"].do(tokens)
				return True
			print(f"Searching for exact value {tokens[0]}...")
			h=self.interface.handle
			mem=system.process_scan_memory(h)
			val=cast(scanner.Scanner.SupportedType,tokens[0])
			self.interface.scanner.continue_search_equal(mem,val)
			self.interface.print_matches()
			return True

	class FindGreater(Command):
		alias:tuple[str,...]=("gt","+")
		description:str="Search for values that increased."
		def do(self,_:'Interface.TokenList')->bool:
			if not self.interface.scanner.is_started(): # TODO: dedup.
				print("Use 'start' first.")
				return False
			print(f"Searching for increased values...")
			h=self.interface.handle
			mem=system.process_scan_memory(h)
			self.interface.scanner.continue_search_greater(mem)
			self.interface.print_matches()
			return True

	class FindLess(Command):
		alias:tuple[str,...]=("lt","-")
		description:str="Search for values that decreased."
		def do(self,_:'Interface.TokenList')->bool:
			if not self.interface.scanner.is_started(): # TODO: dedup.
				print("Use 'start' first.")
				return False
			print(f"Searching for decreased values...")
			h=self.interface.handle
			mem=system.process_scan_memory(h)
			self.interface.scanner.continue_search_less(mem)
			self.interface.print_matches()
			return True

	class Help(Command):
		alias:tuple[str,...]=("help","h","?")
		description:str="Display help."
		def do(self,tokens:'Interface.TokenList')->bool:
			print("Help\n----")
			for c in self.interface.commands:
				a=", ".join(c.alias)
				args=c.arguments
				print("\t",a,args,"\t",c.description)
			return True

	class Poke(Command):
		alias:tuple[str,...]=("poke","p")
		arguments:str="<address> <value>"
		description:str="Write memory."
		def do(self,tokens:'Interface.TokenList')->bool:
			if not self._validate_arguments(tokens,[int|str,int|float]):
				return False
			address=0
			# Handle address as letter 'a' to 'h'
			letters=tuple(chr(ord('a')+i) for i in range(8))
			if tokens[0] in letters:
				address=self.interface.scanner.get_matches()[letters.index(tokens[0])][0]
			else:
				address=cast(int,tokens[0])
			value=tokens[1]
			print(f"Poke {address},{value}... ",end='')
			data=struct.pack(self.interface.scanner.type.code,value)
			ok=system.memory_write(self.interface.handle,address,data)
			print(["ERROR","OK"][int(ok)])
			return True

	class Start(Command):
		alias:tuple[str,...]=("start","s")
		arguments:str="<type> (must be 'int' or 'float')"
		description:str="Start a new search."
		def do(self,tokens:list)->bool:
			if not self._validate_arguments(tokens,[str]):
				return False
			t=tokens[0]
			if t in Interface.SUPPORTED_TYPES:
				print(f"Starting with type {t}.")
				scanner_type={"float":scanner.Scanner.Float32,"int":scanner.Scanner.Int32}[t]
				mem=system.process_scan_memory(self.interface.handle)
				self.interface.scanner.start(mem,scanner_type)
				return True
			else:
				print(f"Invalid type: {t}.")
				print(f"Supported types are {', '.join([x for x in Interface.SUPPORTED_TYPES])}.")
			return False

	SUPPORTED_TYPES="float","int"

	def __init__(self)->None:
		self.scanner=scanner.Scanner()
		self.handle:system.ProcessHandle=None
		self.procinfo:system.ProcessInfo|None=None
		# Create list command objects and fill dictionary.
		self.commands:list['Interface.Command']=[x(self) for x in (
			Interface.Close,
			Interface.FindEqual,
			Interface.FindGreater,
			Interface.FindLess,
			Interface.Help,
			Interface.Poke,
			Interface.Start,
			)]
		self.commands_dict:dict[str,'Interface.Command']={}
		for c in self.commands:
			for a in c.alias:
				self.commands_dict[a]=c

	def __del__(self):
		self.commands_dict["close"].do([])

	def run(self)->None:
		try:
			user_input=""
			while user_input!="q":
				user_input=self._input()
				if user_input in ("exit","quit","q"):
					return
				if user_input:
					tokens=Interface._parse(user_input)
					if self.handle:
						self._command(tokens)
					else:
						self._process_assign(tokens[0])
				elif not self.handle:
					# Show list of processes.
					for k,v in system.get_process_list().items():
						print(f"{k:>8}: {v.name}")
		except KeyboardInterrupt:
			print("Bye!")

	def print_matches(self):
		matches=self.scanner.get_matches()
		num_matches=self.scanner.get_matches_count()
		print(f"{num_matches} matches.")
		if num_matches>8:
			return
		for i,(a,v) in enumerate(matches):
			print(f"{chr(ord('a')+i)}:[{a}]={v}")

	#---------------------------------------------------------------------------

	def _command(self,tokens:list):
		assert self.handle
		# Invoke FindEqual if user typed a number.
		if type(tokens[0]).__name__ in Interface.SUPPORTED_TYPES:
			self.commands_dict["eq"].do(tokens)
			return
		# Invoke command from first token.
		try:
			cmd=self.commands_dict[tokens[0]]
			cmd.do(tokens[1:])
		except KeyError:
			print(f"Unknown command: {tokens[0]}.")

	def _input(self)->str:
		""" Get a string from user. """
		prompt=">"
		if not self.handle:
			print("Enter PID or process name.")
		if self.handle and self.procinfo:
			t=","+self.scanner.get_current_search_type() if self.scanner.is_started() else ""
			prompt=f"<{self.procinfo.pid}:{self.procinfo.name}{t}>"
		user_input=input(prompt)
		return user_input

	def _process_assign(self,entry:Any):
		procs=system.get_process_list()
		if type(entry)==int:
			pid=entry
			if pid in procs:
				#print("ok ",procs[pid])
				self.handle=system.process_open(pid)
				if self.handle:
					self.procinfo=procs[pid] # TODO dedup
			else:
				print("Invalid PID.")
		else:
			name=str(entry).removesuffix(".exe")+".exe"
			pids=Interface._pids_from_process_name(name,procs)
			match len(pids):
				case 0:
					print(f"Process {name} not found.")
				case 1:
					pid=pids[0]
					self.handle=system.process_open(pid)
					if self.handle:
						self.procinfo=procs[pid] # TODO dedup
				case _:
					print(f"PID's for {name} are:")
					print(pids)

	@staticmethod
	def _parse(input_string:str)->TokenList:
		return [number_type(x)(x.lower()) for x in input_string.split()]

	@staticmethod
	def _pids_from_process_name(name:str,proc_dict:dict[system.Pid,system.ProcessInfo])->list[system.Pid]:
		""" Get PID(s) that match a process name. """
		return [k for k,v in proc_dict.items() if v.name.lower()==name]

def main():
	Interface().run()

if __name__=="__main__":
	main()