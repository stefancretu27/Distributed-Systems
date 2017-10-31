echo '>>>The currently running python processes are'
ps aux | grep python

echo 'Do you want to kill all processes[y/n]?'
read answer

if [ "$answer" == "y" ]; then
	echo '>>>Kill all of them'
	kill -9 $(ps aux | grep '[p]ython' | awk '{print $2}')
	echo '>>>The result'
	ps aux | grep python
fi

