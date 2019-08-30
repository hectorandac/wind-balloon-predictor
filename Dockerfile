FROM alpine:3.10.2

RUN apk update
RUN apk add make cmake clang clang-dev libc-dev linux-headers automake gcc g++ subversion python3-dev glib-dev
RUN python3 -m ensurepip
RUN pip3 install --upgrade pip

WORKDIR /opt/predictor
COPY . .
RUN mkdir gfs
RUN pip install -r requirements.txt

WORKDIR /opt/predictor/pred_src
RUN cmake .
RUN make

EXPOSE 3000

WORKDIR /opt/predictor
CMD python3 server.py