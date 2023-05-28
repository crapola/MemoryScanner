"""
Facade to system stuff.
"""
import sys
from dataclasses import dataclass
from typing import Any, TypeAlias,cast

from . import windows
from .windows import memory, processes, win32

if not sys.platform.startswith("win"):
	raise ImportError("Sorry, your OS is not supported.")

MemoryBlocks:TypeAlias=dict[int,bytes]
Pid:TypeAlias=int
ProcessHandle:TypeAlias=Any

@dataclass
class ProcessInfo:
	name:str
	pid:Pid

def get_process_list()->dict[Pid,ProcessInfo]:
	d=windows.processes.processes()
	d={Pid(k):ProcessInfo(v,k) for k,v in d.items()}
	return d

def memory_write(handle:ProcessHandle,address:int,data:bytes)->bool:
	return memory.write(data,handle,address)

def process_close(handle:ProcessHandle)->bool:
	#print(f"win32.CloseProcess({handle})")
	return windows.win32.CloseHandle(handle)

def process_open(pid:Pid)->ProcessHandle:
	#print(f"win32.OpenProcess({pid})")
	PROCESS_ALL_ACCESS=0x001F0FFF
	return windows.win32.OpenProcess(PROCESS_ALL_ACCESS,False,pid)

def process_scan_memory(handle:ProcessHandle)->MemoryBlocks:
	return cast(MemoryBlocks,memory.scan_memory(handle))

def main():
	print(get_process_list())
if __name__=="__main__":
	main()