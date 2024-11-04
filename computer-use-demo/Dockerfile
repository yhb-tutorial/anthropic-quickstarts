FROM docker.io/ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_PRIORITY=high

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install \
    # SSH Server
    openssh-server \
    build-essential \
    # UI Requirements
    xvfb \
    xterm \
    xdotool \
    scrot \
    imagemagick \
    sudo \
    mutter \
    x11vnc \
    # Python/pyenv reqs
    build-essential \
    libssl-dev  \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    curl \
    git \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    # Network tools
    net-tools \
    netcat \
    # PPA req
    software-properties-common && \
    # Userland apps
    sudo add-apt-repository ppa:mozillateam/ppa && \
    sudo apt-get install -y --no-install-recommends \
    libreoffice \
    firefox-esr \
    x11-apps \
    xpdf \
    gedit \
    xpaint \
    tint2 \
    galculator \
    pcmanfm \
    unzip && \
    apt-get clean

# Install noVNC
RUN git clone --branch v1.5.0 https://github.com/novnc/noVNC.git /opt/noVNC && \
    git clone --branch v0.12.0 https://github.com/novnc/websockify /opt/noVNC/utils/websockify && \
    ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html

# SSH服务器配置
RUN mkdir /var/run/sshd
# 设置computeruse用户的密码为'computeruse'
RUN echo 'computeruse:computeruse' | chpasswd
# 允许使用密码登录
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
# 允许SSH登录
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# 配置SSH监听所有接口
RUN echo "ListenAddress 0.0.0.0" >> /etc/ssh/sshd_config
RUN echo "AddressFamily any" >> /etc/ssh/sshd_config

# SSH登录修复
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd



# 设置环境变量
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# setup user
ENV USERNAME=computeruse
ENV HOME=/home/$USERNAME
RUN useradd -m -s /bin/bash -d $HOME $USERNAME && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    mkdir -p $HOME/.ssh && \
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDIkZttXbZOHA02PWwrmhkeyhUoUZR+HrRJYEba5ZNLAxjK8W/8+jYFtXEKT3rpWcpy6Abr2DwZa823zyPv7S717dQ5da/hCXzFcJBeYHQHa9qlvrvZTH0QOWSCV1Ng+F3lOc5fFPHz9H/VoTVz3KmimJedCDl/wlsEJhmJ3gTsXqiX2kg+2rjukNql+5Qu4r76K9sBU1t5NzcBGo75UJ5lA4Ol/eWa+i2lzBv9NTzhmIolz/QbiPR7ihAHJyYiH5HpSh5aqH5sSCLy/Ke6+7R3Asj9PbiMGmoaeNFW8JZuApzwC5KOfksBmKTJ/FYiTeygKsKRG1kusHs1OuGE2Qh+Sog82oOAUJqv5Jz9PfGwg9p2pUy3kdRgptHNIiABIyCEmTFG8M+CZJalijD52uK0ChuxhCLCh4RmrXZ+pMNIQU9iWtNvxgfqai+RAFBQ5bOXwxU1fND6+cKCoCQvLFDsPSK598IcnShadVvjt1u2aFngN/X32NfL695MGTpEZ2M= yanghaibin@YHB-MacBook.local" > $HOME/.ssh/authorized_keys && \
    chmod 700 $HOME/.ssh && \
    chmod 600 $HOME/.ssh/authorized_keys && \
    chown -R $USERNAME:$USERNAME $HOME/.ssh
USER computeruse
WORKDIR $HOME

# setup python
RUN git clone https://github.com/pyenv/pyenv.git ~/.pyenv && \
    cd ~/.pyenv && src/configure && make -C src && cd .. && \
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
ENV PYENV_ROOT="$HOME/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"
ENV PYENV_VERSION_MAJOR=3
ENV PYENV_VERSION_MINOR=11
ENV PYENV_VERSION_PATCH=6
ENV PYENV_VERSION=$PYENV_VERSION_MAJOR.$PYENV_VERSION_MINOR.$PYENV_VERSION_PATCH
RUN eval "$(pyenv init -)" && \
    pyenv install $PYENV_VERSION && \
    pyenv global $PYENV_VERSION && \
    pyenv rehash

ENV PATH="$HOME/.pyenv/shims:$HOME/.pyenv/bin:$PATH"

RUN python -m pip install --upgrade pip==23.1.2 setuptools==58.0.4 wheel==0.40.0 && \
    python -m pip config set global.disable-pip-version-check true

# 新增 FastAPI 相关依赖
RUN python -m pip install fastapi uvicorn 

# only reinstall if requirements.txt changes
COPY --chown=$USERNAME:$USERNAME computer_use_demo/requirements.txt $HOME/computer_use_demo/requirements.txt
RUN python -m pip install -r $HOME/computer_use_demo/requirements.txt

# setup desktop env & app
COPY --chown=$USERNAME:$USERNAME image/ $HOME
COPY --chown=$USERNAME:$USERNAME computer_use_demo/ $HOME/computer_use_demo/

ARG DISPLAY_NUM=1
ARG HEIGHT=768
ARG WIDTH=1024
ENV DISPLAY_NUM=$DISPLAY_NUM
ENV HEIGHT=$HEIGHT
ENV WIDTH=$WIDTH

# 暴露所需端口
EXPOSE 22 5900 8501 6080 8080 8000

ENTRYPOINT [ "./entrypoint.sh" ]
