# Builds the single-file `rsc` executable against the glibc of RHEL 9.
FROM rockylinux:9

ARG PYTHON_VERSION=3.14.7
ENV PYTHON_PREFIX=/opt/python \
    LD_LIBRARY_PATH=/opt/python/lib

RUN dnf -y install --setopt=install_weak_deps=False \
        gcc gcc-c++ make tar xz findutils binutils \
        zlib-devel bzip2-devel xz-devel openssl-devel libffi-devel \
        sqlite-devel readline-devel ncurses-devel \
    && dnf clean all

RUN curl -fsSL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz" \
        -o /tmp/python.tar.xz \
    && tar -xf /tmp/python.tar.xz -C /tmp \
    && cd "/tmp/Python-${PYTHON_VERSION}" \
    && ./configure --prefix="${PYTHON_PREFIX}" --enable-shared --without-static-libpython \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /tmp/Python-* /tmp/python.tar.xz

ENV PATH="${PYTHON_PREFIX}/bin:${PATH}"

WORKDIR /src
COPY vendor /src/vendor
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-index --find-links /src/vendor/build-wheels \
        -r /src/vendor/requirements-build.txt \
    && /opt/venv/bin/pip install --no-index --find-links /src/vendor/wheels \
        -r /src/vendor/requirements.txt

COPY pyproject.toml /src/pyproject.toml
COPY src /src/src
COPY config /src/config
COPY build /src/build

RUN /opt/venv/bin/pyinstaller --clean --noconfirm \
        --distpath /src/dist --workpath /src/.pyinstaller \
        /src/build/rsc.spec \
    && /src/dist/rsc --help > /dev/null

CMD ["cp", "/src/dist/rsc", "/out/rsc"]
