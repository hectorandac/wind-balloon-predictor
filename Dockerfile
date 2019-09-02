FROM alpine:3.10.2

RUN apk update
RUN apk add make cmake clang clang-dev libc-dev linux-headers automake gcc g++ subversion glib-dev python2-dev
RUN python2 -m ensurepip
RUN pip install --upgrade pip

WORKDIR /opt/predictor
COPY . .
RUN mkdir gfs
RUN pip install -r requirements.txt

WORKDIR /opt/predictor/pred_src
RUN cmake .
RUN make

EXPOSE 5000

WORKDIR /opt/predictor
CMD python server.py