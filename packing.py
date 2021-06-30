import struct

def pack_list(format:str,data:list)->bytes:
	return struct.pack(f"{len(data)}{format}",*data)

def unpack_list(format:str,data:bytes)->list:
	size=struct.calcsize(format)
	return struct.unpack(f"{len(data)//size}{format}",data)

if __name__=="__main__":
	numbers=(65,100,80,120)
	p=pack_list("q",numbers)
	print("pack=",p)
	up=unpack_list("b",p)
	print("unpack=",up)