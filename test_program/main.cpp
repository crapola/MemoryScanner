#include <chrono>
#include <iostream>
#include <thread>

int main(int,char**)
{
	std::wcout<<"Hello\n";
	auto foo=std::wstring(L"Test program status: ");
	for (int i=0;i<100;++i)
	{
		std::wcout<<foo<<"i="<<i<<"\n";
		std::this_thread::sleep_for(std::chrono::seconds(10));
	}
}