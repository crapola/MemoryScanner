# Mess around with Notepad memory.
import memory
import processes
from win32 import PROCESS_ALL_ACCESS, CloseHandle, OpenProcess, PrintLastError

def main():
	pid=processes.find_pid_by_process_name("notepad.exe")
	handle=OpenProcess(PROCESS_ALL_ACCESS,False,pid)
	if handle:
		result=memory.scan_memory(handle)
		offsets=result.search("Windows".encode("utf-16")[2:])
		for o in offsets:
			print("Found at ",o)
			print(memory.write("Hello!  ".encode("utf-16")[2:],handle,o))
		CloseHandle(handle)
	else:
		print("Notepad isn't running.")
		PrintLastError("OpenProcess")
	print("Done.")

if __name__=="__main__":
	main()
