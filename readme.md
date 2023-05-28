## MemoryScanner

This is a memory scanner for Windows written in Python that runs in the console.

### Dependencies
It requires Numpy.

### Usage
Run with `python MemoryScanner`.

#### Commands
Once a process is opened, these commands are available:

- start / s (type)<br>
	Initiate search with given type.<br>
	Supported types are 'int' for int32 or 'float' for float32.

- eq / = (value)<br>
	Look for exact value.<br>
	The eq command is optional, you can also just type the value by itself.

- gt / +<br>
	Look for values that increased.

- lt / -<br>
	Look for values that decreased.

- poke / p (address or letter) (value)<br>
	Write memory by address integer or by one of the letters shown in results.
	Value is int of float (with decimal point).

- close<br>
	Close current process and go back to process selection.

- help / h / ?<br>
	Display help.