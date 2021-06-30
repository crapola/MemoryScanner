from ctypes import (POINTER, WINFUNCTYPE, GetLastError, Structure, c_ulonglong,
                    c_void_p, windll)
from ctypes.wintypes import (BOOL, DWORD, HANDLE, HMODULE, LPCVOID, LPDWORD,
                             LPSTR, LPVOID, LPWSTR, WORD)

# Types
# -----

PVOID=c_void_p
SIZE_T=c_ulonglong

class MEMORY_BASIC_INFORMATION(Structure):
	_fields_=[
		("BaseAddress",PVOID),
		("AllocationBase",PVOID),
		("AllocationProtect",DWORD),
		("PartitionId",WORD),
		("RegionSize",SIZE_T),
		("State",DWORD),
		("Protect",DWORD),
		("Type",DWORD)
	]
	def info(self)->str:
		s=""
		s=s+f"BaseAddress: {self.BaseAddress or 0}\n"
		s=s+f"AllocationBase: {self.AllocationBase or 0}\n"
		s=s+f"AllocationProtect: {MemoryProtectionConstantString(self.AllocationProtect)}\n"
		s=s+f"PartitionId: {self.PartitionId}\n"
		s=s+f"RegionSize: {self.RegionSize}\n"
		state_string="MEM_COMMIT" if self.State==0x1000 else\
			"MEM_FREE" if self.State==0x10000 else\
			"MEM_RESERVE" if self.State==0x2000 else\
			str(self.State)
		s=s+f"State: {state_string}\n"
		s=s+f"Protect: {MemoryProtectionConstantString(self.Protect)}\n"
		type_string="MEM_IMAGE" if self.Type==0x1000000 else\
			"MEM_MAPPED" if self.Type==0x40000 else\
			"MEM_PRIVATE" if self.Type==0x20000 else\
			str(self.Type)
		s=s+f"Type: {type_string}\n"
		return s

	def can_read(self)->bool:
		return self.AllocationProtect==0x04 and self.Protect!=0x01 and self.Protect!=0

PMEMORY_BASIC_INFORMATION=POINTER(MEMORY_BASIC_INFORMATION)

# Constants
# ---------

def ErrorCodeString(error):
	return\
		"ERROR_ACCESS_DENIED" if error==5 else\
		"ERROR_INVALID_HANDLE" if error==6 else\
		"ERROR_BAD_LENGTH" if error==24 else\
		"ERROR_INVALID_PARAMETER" if error==87 else\
		"ERROR_PARTIAL_COPY" if error==299 else\
		str(error)

def PrintLastError(function_name):
	error=GetLastError()
	print(f"{function_name} failed with error {ErrorCodeString(error)}.")

def MemoryProtectionConstantString(value):
		return\
			"PAGE_EXECUTE" if value==0x10 else\
			"PAGE_EXECUTE_READ" if value==0x20 else\
			"PAGE_EXECUTE_READWRITE" if value==0x40 else\
			"PAGE_EXECUTE_WRITECOPY" if value==0x80 else\
			"PAGE_NOACCESS" if value==0x01 else\
			"PAGE_READONLY" if value==0x02 else\
			"PAGE_READWRITE" if value==0x04 else\
			"PAGE_WRITECOPY" if value==0x08 else\
			"PAGE_TARGETS_INVALID" if value==0x40000000 else\
			"PAGE_TARGETS_NO_UPDATE" if value==0x40000000 else\
			"0 (no access)" if value==0 else\
			str(value)

PROCESS_ALL_ACCESS=0x001F0FFF

# Functions
# ---------

# paramflags:
# 1 Specifies an input parameter to the function.
# 2 Output parameter. The foreign function fills in a value.
# 4 Input parameter which defaults to the integer zero.

CloseHandle=WINFUNCTYPE(BOOL,HANDLE)( ("CloseHandle",windll.kernel32),
((1,"hObject"),))
EnumProcesses=WINFUNCTYPE(DWORD,POINTER(DWORD),DWORD,LPDWORD)(("EnumProcesses",windll.psapi),
((1,"lpidProcess"),(1,"cb"),(1,"lpcbNeeded")))
EnumProcessModulesEx=WINFUNCTYPE(BOOL,HANDLE,POINTER(HMODULE),DWORD,LPDWORD,DWORD)(("EnumProcessModulesEx",windll.psapi),
((1,"hProcess"),(1,"lphModule"),(1,"cb"),(1,"lpcbNeeded"),(1,"dwFilterFlag")))
GetModuleBaseName=WINFUNCTYPE(DWORD,HANDLE,HMODULE,LPWSTR,DWORD)(("GetModuleBaseNameW",windll.psapi),
((1,"hProcess"),(1,"hModule"),(1,"lpBaseName"),(1,"nSize")))
GetProcessImageFileNameA=WINFUNCTYPE(DWORD,HANDLE,LPSTR,DWORD)(("GetProcessImageFileNameA",windll.psapi),
((1,"hProcess"),(1,"lpImageFileName"),(1,"nSize")))
OpenProcess=WINFUNCTYPE(HANDLE,DWORD,BOOL,DWORD)(("OpenProcess",windll.kernel32),
((1,"dwDesiredAccess"),(1,"bInheritHandle"),(1,"dwProcessId")))
ReadProcessMemory=WINFUNCTYPE(BOOL, HANDLE,LPCVOID,LPVOID,SIZE_T,POINTER(SIZE_T))(("ReadProcessMemory",windll.kernel32),
((1,"hProcess"),(1,"lpBaseAddress"),(1,"lpBuffer"),(1,"nSize"),(1,"lpNumberOfBytesRead")))
WriteProcessMemory=WINFUNCTYPE(BOOL, HANDLE,LPCVOID,LPVOID,SIZE_T,POINTER(SIZE_T))(("WriteProcessMemory",windll.kernel32),
((1,"hProcess"),(1,"lpBaseAddress"),(1,"lpBuffer"),(1,"nSize"),(1,"lpNumberOfBytesWritten")))
VirtualQueryEx=WINFUNCTYPE(SIZE_T,HANDLE,LPCVOID,PMEMORY_BASIC_INFORMATION,SIZE_T)(("VirtualQueryEx",windll.kernel32),
((1,"hProcess"),(1,"lpAddress"),(1,"lpBuffer"),(1,"dwLength")))
