FROM archlinux:latest

ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"

RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
    git \
    base-devel \
    pyenv \
    sdl2_image \
    sdl2-compat \
    tk \
    libffi \
    zlib \
    bzip2 \
    readline \
    neovim \
    xclip \
    sqlite && \
    ln -sf /usr/lib/libGLX_indirect.so.0 /usr/lib/libGLX_indirect.so.0

RUN pyenv install 3.12.12 && \
    pyenv global 3.12.12

WORKDIR /root/Principia

RUN git clone https://github.com/oceanthunder/Principia.git .

RUN pip install --no-cache-dir -r requirements.txt

RUN cd SDLPoP/src && make shared

WORKDIR /root/Principia

CMD ["/bin/bash"]

