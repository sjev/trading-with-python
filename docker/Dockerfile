FROM python:latest

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# install python stuff
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /workspaces/notebooks

CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]