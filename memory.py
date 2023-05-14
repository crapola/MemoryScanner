from collections.abc import MutableMapping
from ctypes import byref, create_string_buffer, sizeof
from ctypes.wintypes import HANDLE, LPCVOID
from typing import Tuple

from win32 import (MEMORY_BASIC_INFORMATION, SIZE_T, PrintLastError,
                   ReadProcessMemory, VirtualQueryEx, WriteProcessMemory)

class MemoryBlocks(MutableMapping):
	""" Dictionary Dict[int,bytes] """
	def __init__(self,*args,**kw):
		self._store=dict(*args,**kw)

	def __delitem__(self,v:bytes)->None:
		return self._store.__delitem__(v)

	def __getitem__(self,k:int)->bytes:
		return self._store.__getitem__(k)

	def __iter__(self)->iter:
		return self._store.__iter__()

	def __len__(self)->int:
		return self._store.__len__()

	def __setitem__(self,k:int,v:bytes)->None:
		assert isinstance(k,int),"key must be integer."
		assert isinstance(v,bytes),"value must be bytes."
		return self._store.__setitem__(k,v)

	def __str__(self)->str:
		s=f"MemoryBlocks {len(self._store)} entries:\n"
		for k,v in self._store.items():
			s=s+f"\t{str(k)}: {len(v)} Bytes\n"
		return s

	def defrag(self)->None:
		""" Combine adjacent blocks. """
		prev=(None,None,None)
		for k,v in list(self._store.items()):
			p_k,p_v,p_acc=prev
			if p_acc==k:
				self._store.pop(k)
				self._store[p_k]=p_v+v
			prev=(k,v,k+len(v))

	def get_value(self,address:int):
		""" Get value from address. Return None if address not in blocks. """
		addresses=list(filter(lambda x:x<=address,self._store.keys()))
		if len(addresses)==0:
			return None
		closest_block=min(addresses,key=lambda x:abs(x-address))
		offset=address-closest_block
		if offset>=len(self._store.__getitem__(closest_block)):
			return None
		return self._store.__getitem__(closest_block)[offset]

	def search(self,what:bytes)->Tuple[int]:
		results=[]
		for k,v in self._store.items():
			found=0
			while found>-1:
				found=v.find(what,found)
				if found>-1:
					results.append(k+found)
					found+=len(what)
		return tuple(results)

	def size(self)->int:
		result=0
		for v in self._store.values():
			result=result+len(v)
		return result

def scan_memory(handle:HANDLE)->MemoryBlocks:
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
	return MemoryBlocks(result)

def write(data:bytes,handle:HANDLE,address:LPCVOID)->bool:
	size_written=SIZE_T()
	return WriteProcessMemory(handle,address,data,len(data),size_written)

def main():
	m=MemoryBlocks({123:[45,0,1,2],127:[55,54],500:[500]*40})
	print(m)
	print(m.get_value(127))
	print(m.get_value(128))
	print(m.get_value(129))
	print(m.get_value(539))
if __name__=="__main__":
	main()