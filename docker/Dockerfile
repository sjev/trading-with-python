FROM python:latest

ENV LANG en_US.UTF-8

ARG USERNAME=nerd
ARG USER_UID
ARG USER_GID

# Check for mandatory build arguments
RUN : "${USER_UID:?Build argument needs to be set and non-empty.}" && \
    : "${USER_GID:?Build argument needs to be set and non-empty.}"

# setup locale
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y locales apt-utils
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure locales && \
    update-locale LANG=en_US.UTF-8


# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME



# install python stuff
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# create notebook mount point
RUN mkdir -p /notebooks
RUN chown -R $USERNAME:$USERNAME /notebooks

# copy start scripts
COPY files/start_jupyter_lab.sh  /
RUN chmod 777 /start_jupyter_lab.sh
#  -------------local user -----------------------
# Set the default user. Omit if you want to keep the default as root.
USER $USERNAME

RUN echo 'export PS1="🤓  \[\033[1;36m\]\h \[\e[33m\]\W\[\e[m\] \[\033[1;36m\]# \[\033[0m\]"' >> ~/.bashrc



# copy notebook settings
RUN mkdir -p /home/$USERNAME/.jupyter
COPY jupyter_notebook_config.py /home/$USERNAME/.jupyter/jupyter_notebook_config.py

# finalize
WORKDIR /notebooks

EXPOSE 8888
CMD ["/start_jupyter_lab.sh" ]