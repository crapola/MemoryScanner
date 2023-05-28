from ctypes import byref, create_string_buffer, sizeof
from ctypes.wintypes import HANDLE, LPCVOID

from .win32 import (MEMORY_BASIC_INFORMATION, SIZE_T, PrintLastError,
                    ReadProcessMemory, VirtualQueryEx, WriteProcessMemory)


def scan_memory(handle:HANDLE)->dict[int,bytes]:
	mem_info=MEMORY_BASIC_INFORMATION()
	addr=0
	result={}
	while addr<0x7FFFFFFFFFF:
		x=VirtualQueryEx(handle,addr,byref(mem_info),sizeof(mem_info))
		if x>0:
			addr=(mem_info.BaseAddress or 0)+mem_info.RegionSize
			if mem_info.can_read():
				buffer=create_string_buffer(mem_info.RegionSize)
				size_read=SIZE_T()
				x=ReadProcessMemory(handle,mem_info.BaseAddress,byref(buffer),mem_info.RegionSize,byref(size_read))
				if x:
					#print(f"Read {size_read.value} bytes.")
					result[mem_info.BaseAddress]=buffer.raw
				else:
					PrintLastError("ReadProcessMemory")
		else:
			PrintLastError("VirtualQueryEx")
			break
	return result

def write(data:bytes,handle:HANDLE,address:LPCVOID|int)->bool:
	size_written=SIZE_T()
	return WriteProcessMemory(handle,address,data,len(data),size_written)

