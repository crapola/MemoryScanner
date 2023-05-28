import time
from typing import Any, Callable, TypeAlias

import numpy as np

import pretty

NumpyArray:TypeAlias=np.ndarray

Memory:TypeAlias=dict[int,bytes] # key=base address, value=raw data bytes.

Matches:TypeAlias=dict[int,NumpyArray] # key=base address, value=converted data.

Criterion:TypeAlias=Callable[[NumpyArray,NumpyArray,Any],NumpyArray]

class Scanner:

	SupportedType:TypeAlias=float|int

	class Type:
		code:str=""
		name:str="Base Type"
		numpy_type=None
		size:int=4
	class Int32(Type):
		code="i"
		name="Int32"
		numpy_type=np.int32
	class Float32(Type):
		code="f"
		name="Float32"
		numpy_type=np.single
	class Float64(Type):
		code="d"
		name="Float64"
		numpy_type=np.double
		size=8

	def __init__(self)->None:
		self.type:type[Scanner.Type]=Scanner.Type

	def continue_search_equal(self,mem:Memory,value:SupportedType):
		self.search(mem,value,Scanner.cmp_eq)

	def continue_search_greater(self,mem:Memory):
		self.search(mem,0,Scanner.cmp_gt)

	def continue_search_less(self,mem:Memory):
		self.search(mem,0,Scanner.cmp_lt)

	def get_current_search_type(self)->str:
		return self.type.name

	def get_matches_count(self)->int:
		if not self.matches_offsets:
			return 0
		return sum([len(v) for v in self.matches_offsets.values()])

	def get_matches(self)->tuple[tuple[int,SupportedType],...]:
		""" Get up to 8 first matches. """
		if not self.matches_offsets:
			return ()
		ret=[]
		size=self.type.size
		for k,offs in self.matches_offsets.items():
			abs_addr=[int(k+x*size) for x in offs]
			value=[self.matches[k][off] for off in offs]
			ret+=(list(zip(abs_addr,value)))
			if len(ret)>=8:
				ret=ret[:8]
				break
		return tuple(sorted(ret))

	def is_started(self)->bool:
		return self.type!=Scanner.Type

	def start(self,mem:Memory,stype:type[Type]):
		""" Initiate a search with given type. """
		assert stype!=Scanner.Type,f"Invalid search type: {stype}"
		#print(f"Starting search for type {stype.name}.")
		self.type=stype
		# Initialize matches to everything.
		self.matches=Scanner._convert(mem,stype)
		self.matches_offsets=None
		num_bytes=Scanner._count_matches(self.matches)*self.type.size
		print(f"Scanned {pretty.pretty_size(num_bytes)}.")

	#---------------------------------------------------------------------------

	# Criteria used in _search.
	@staticmethod
	def cmp_eq(old:NumpyArray,new:NumpyArray,val)->NumpyArray:
		return np.where(new==val)[0]

	@staticmethod
	def cmp_gt(old:NumpyArray,new:NumpyArray,val)->NumpyArray:
		return np.where(old<new)[0]

	@staticmethod
	def cmp_lt(old:NumpyArray,new:NumpyArray,val)->NumpyArray:
		try:
			return np.where(old>new)[0]
		except ValueError:
			print("old=",old,old.size)
			print("new=",new,new.size)
			raise

	def search(self,mem:Memory,value:SupportedType,criterion:Criterion):
		assert self.type!=Scanner.Type,"Search type not provided."
		time_now=time.time()
		keys_in_common=self.matches.keys() & mem.keys()
		intersection={k:mem[k] for k in keys_in_common}
		matches={}
		matching_offsets={}
 		# TODO: Optimize memory usage.
		for base_address,region_bytes in intersection.items():
			data:NumpyArray=np.frombuffer(region_bytes,self.type.numpy_type)
			previous=self.matches[base_address]
			#assert len(previous)==len(data)
			if len(previous)!=len(data):
				print(f"Region {base_address} had different size.")
				continue
			indices=criterion(previous,data,value)
			if len(indices)>0:
				matches[base_address]=data
				if self.matches_offsets:
					matching_offsets[base_address]=self.matches_offsets[base_address] & set(indices)
				else:
					matching_offsets[base_address]=set(indices)
		print(f"Search completed in {time.time()-time_now:.5} seconds.")
		self.matches=matches
		self.matches_offsets=matching_offsets

	@staticmethod
	def _count_matches(matches:Matches)->int:
		return sum(len(x) for x in matches.values())

	@staticmethod
	def _convert(mem:Memory,type:type[Type])->dict:
		return {k:np.frombuffer(v,type.numpy_type) for k,v in mem.items()}