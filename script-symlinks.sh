#!/bin/bash

echo "server.py"
diff ../server.py server.py
if [[ -f ../server.py ]]; then
    mv ../server.py /tmp
fi
ln -s utils/server.py ..

echo "client.sh"
diff ../client.sh client.sh
if [[ -f ../client.sh ]]; then
    mv ../client.sh /tmp
fi
ln -s utils/client.sh ..
