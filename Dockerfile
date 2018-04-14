FROM python:3.6.5-alpine3.7
RUN pip install tornado==4.1.0
RUN pip install tornado-redis==2.4.18
COPY apps/chat_server /apps/chat_server
ENTRYPOINT /bin/sh
WORKDIR /apps/chat_server
CMD /bin/python main.py
