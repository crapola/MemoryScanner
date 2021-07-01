import ctypes
from ctypes import sizeof
from ctypes.wintypes import DWORD, HANDLE, HMODULE, WCHAR
from typing import Dict, Tuple

from win32 import (CloseHandle, EnumProcesses, EnumProcessModulesEx,
                   GetModuleBaseName, GetProcessImageFileNameA, OpenProcess,
                   PrintLastError)


def get_all_process_ids()->Tuple[int]:
	"""
	Return list of running processes PIDs.
	"""
	buffer=(DWORD*1024)()
	size_used=DWORD()
	ok=EnumProcesses(buffer,len(buffer),size_used)
	if not ok:
		PrintLastError("EnumProcesses")
		return tuple()
	count=size_used.value//ctypes.sizeof(DWORD)
	return tuple(buffer[:count])

# https://docs.microsoft.com/en-us/windows/win32/psapi/enumerating-all-processes
def processes()->Dict[int,str]:
	"""
	Return running processes as a dictionary where keys are PIDs and values are
	process names.
	"""
	def process_name(pid:int)->str:
		szprocessname=ctypes.create_unicode_buffer(256)
		hprocess=OpenProcess(0x410,False,pid)
		if hprocess:
			hmod=HMODULE()
			cbneeded=DWORD()
			if EnumProcessModulesEx(hprocess,hmod,sizeof(hmod),cbneeded,0x00):
				nsize=DWORD(sizeof(szprocessname)//sizeof(WCHAR))
				returned_size=GetModuleBaseName(hprocess,hmod,szprocessname,nsize)
				if returned_size==0:
					PrintLastError("GetModuleBaseName")
			else:
				PrintLastError("EnumProcessModulesEx")
			if not CloseHandle(hprocess):
				PrintLastError("CloseHandle")
		else:
			# OpenProcess is expected to fail for some PIDs.
			# PrintLastError("OpenProcess")
			return None
		return szprocessname.value
	pids=get_all_process_ids()
	if not pids:
		return tuple()
	result={}
	for p in pids:
		name=process_name(p)
		if name:
			result[p]=name
	return result

def find_pid_by_process_name(name:str)->int:
	"""
	Find the first PID associated with executable name.
	Return -1 if no match.
	TODO: return all of them...
	"""
	procs=processes()
	for k,v in sorted(procs.items()):
		print(f"{k}: '{v}'")
	try:
		return list(procs.keys())[list(procs.values()).index(name)]
	except ValueError:
		return -1

def process_name(handle:HANDLE)->str:
	name=ctypes.create_string_buffer(256)
	string_length=GetProcessImageFileNameA(handle,name,256)
	return name.value.decode('ansi')
