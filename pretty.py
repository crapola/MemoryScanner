from typing import Collection

# Taken from https://stackoverflow.com/a/12912296
def pretty_size(s)->str:
	units=[
		(1<<50,' PB'),
		(1<<40,' TB'),
		(1<<30,' GB'),
		(1<<20,' MB'),
		(1<<10,' KB'),
		(1,(' Byte',' Bytes')),
	]
	factor,suffix=units[-1]
	for factor,suffix in units:
		if s>=factor:
			break
	amount=s/factor
	if factor==1:
		amount=int(amount)
	if isinstance(suffix, tuple):
		singular,multiple=suffix
		if amount==1:
			suffix=singular
		else:
			suffix=multiple
	return str(amount)+suffix

def format_big_list(lst:Collection)->str:
	lst_str=','.join([str(x) for x in tuple(lst)[0:5]])
	if len(lst)>10:
		return f"{lst_str} and {len(lst)-5} more... "
	else:
		return lst_str

if __name__=="__main__":
	print(pretty_size(-100))
	print(pretty_size(0))
	print(pretty_size(1000))
	print(pretty_size(10000000))
	print(format_big_list([1]*10))
	print(format_big_list([1]*12))
	print(format_big_list([1]*100))
	print(format_big_list(set([x*2 for x in range(0,200)])))