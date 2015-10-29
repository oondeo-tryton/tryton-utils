FROM nantic/tryton-base
ADD . /root/tryton
WORKDIR /root/tryton
EXPOSE 8000
ENTRYPOINT ./server.py start
