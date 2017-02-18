#!/bin/bash

dbpath=`mktemp -d db.XXXX`
echo "[+] database path: ${dbpath}"

pass=`tr -cd '[:alnum:]' < /dev/urandom | fold -w30 | head -n1`
image=`docker run -v $dbpath:/var/lib/mysql -d -e MYSQL_ROOT_PASSWORD=$pass mysql`
ip=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $image`

echo "[+] mysql host: ${ip}"
echo "[+] mysql user: root"
echo "[+] mysql pass: ${pass}"

sleep 30 # mysql should complete loading

mysql -u root -h ${ip} -p${pass} < init.sql 2>/dev/null

sleep 2

./checker.py 0.0.0.0 14900 ${ip} root ${pass} &
./web.py 0.0.0.0 8080 ${ip} root ${pass} &
#./zond.py root ${pass} &

echo "[+] done"
wait
