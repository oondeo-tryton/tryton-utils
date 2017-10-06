FROM nantic/tryton
ADD . /root/tryton
WORKDIR /root/tryton
EXPOSE 8000
ENTRYPOINT ./server.py start
