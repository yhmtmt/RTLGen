FROM ubuntu:22.04

# Prvent tzdata from prompting for geographic area
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    eog \
    lxterminal \
    emacs \
    time \
    wget \
    build-essential \
    bison \
    ca-certificates \
    cmake \
    flex \
    git \
    gdb \
    gnupg \
    liblemon-dev \
    libeigen3-dev \
    libgtest-dev \
    libspdlog-dev \
    libfl-dev \
    libbz2-dev \
    liblzma-dev \
    libzstd-dev \
    lsb-release \
    libtool \
    autoconf \
    automake \
    python3 \
    python3-pip \
    swig \
    tcl-dev \
    libtk8.6 \
    tk-dev \
    x11-apps \
    libx11-dev \
    libxrender1 \
    libxtst6 \
    libxi6 \
    xauth \    
    iverilog \
    gtkwave \
    jq \
    libyaml-cpp-dev \
    tzdata && \

    ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

    # for autotuner
RUN apt-get update && apt-get install -y python3-venv

RUN apt-get update && apt-get install -y qtbase5-dev libqt5charts5-dev qttools5-dev qttools5-dev-tools libqt5widgets5 libqt5svg5-dev


RUN git clone https://github.com/ivmai/cudd.git /tmp/cudd && \
    cd /tmp/cudd && \
    autoreconf -i && \
    ./configure --prefix=/usr/local && \
    make -j$(nproc) && make install && \
    rm -rf /tmp/cudd
    
RUN pip3 install PyYAML

# OpenROAD requires boost version >=1.78, 1.74 default in Ubuntu 22.04. The latest version is retrieved.
RUN add-apt-repository ppa:mhier/libboost-latest && \
    apt update && \
    apt-get install -y $(apt-cache search --names-only '^libboost[0-9\.]+-all-dev$' | sort -V | tail -n 1 | awk '{print $1}')

RUN apt-get update && apt-get install -y gdebi-core \
 && wget -O /tmp/klayout.deb https://www.klayout.org/downloads/Ubuntu-22/klayout_0.30.2-1_amd64.deb \
 && gdebi -n /tmp/klayout.deb \
 && rm /tmp/klayout.deb \
 && wget -O /tmp/oss-cad-suite.tgz https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2025-07-18/oss-cad-suite-linux-x64-20250718.tgz \
 && tar -C / -xzf /tmp/oss-cad-suite.tgz \
 && rm /tmp/oss-cad-suite.tgz

# Download and install OR-Tools
RUN wget https://github.com/google/or-tools/releases/download/v9.10/or-tools_amd64_ubuntu-22.04_cpp_v9.10.4067.tar.gz && \
    tar -xzf or-tools_amd64_ubuntu-22.04_cpp_v9.10.4067.tar.gz && \
    EXTRACTED_DIR=$(tar -tf or-tools_amd64_ubuntu-22.04_cpp_v9.10.4067.tar.gz | head -1 | cut -f1 -d"/") && \
    cp -r ${EXTRACTED_DIR}/include/* /usr/local/include/ && \
    cp -r ${EXTRACTED_DIR}/lib/* /usr/local/lib/ && \
    cp -r ${EXTRACTED_DIR}/bin/* /usr/local/bin/ && \
    ldconfig && \
    rm or-tools_amd64_ubuntu-22.04_cpp_v9.10.4067.tar.gz && \
    rm -rf ${EXTRACTED_DIR}

#RUN git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD.git &&    cd OpenROAD &&    mkdir build &&    cd build && \
#    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_GUI=on && \    
#    make -j$(nproc) && \
#    make install

RUN git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD.git && \
    cd OpenROAD && \
    git checkout 320b89c852344bf1a6e7e7889c3a6c96e3cc067b && \
    git submodule update --init --recursive && \
    # Ensure the specific submodule commits are checked out before building
    git -C src/sta fetch --all && git -C src/sta checkout 05b292c379c9f3a74d23c67adb6f937e0206b374 && \
    git -C third-party/abc fetch --all && git -C third-party/abc checkout 2bf0bb0ce35cda283d69c8b70c8e668e8511adc1 && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_GUI=on && \
    make -j$(nproc) && \
    make install

# Clone the repository checkout 1f4e76eb5a7758c813ccca3b555bed6258870cad and apply RTLGen/bugfix-autotuner.patch
#RUN git clone https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git /orfs && cd orfs && git checkout 1f4e76eb5a7758c813ccca3b555bed6258870cad && git submodule update --init --recursive && git apply /workspaces/RTLGen/RTLGen/bugfix-autotuner.patch
RUN git clone https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git /orfs && \
    cd orfs && git checkout 1f4e76eb5a7758c813ccca3b555bed6258870cad 
COPY bugfix-autotuner.patch /orfs/bugfix-autotuner.patch
RUN cd orfs && git submodule update --init --recursive && git apply /orfs/bugfix-autotuner.patch

RUN python3 -m pip install --upgrade pip setuptools wheel 

RUN /orfs/tools/AutoTuner/installer.sh && /orfs/tools/AutoTuner/setup.sh 


ENV PATH="/oss-cad-suite/bin:/orfs/tools/AutoTuner/autotuner_env/bin:/workspaces/RTLGen/bin:${PATH}"
ENV OPENROAD_EXE="/usr/bin/openroad"
ENV YOSYS_EXE="/oss-cad-suite/bin/yosys"
ENV LD_LIBRARY_PATH="/usr/bin/:${PATH}"

# Install ONNX Runtime
# Set ONNX_VERSION to the desired version, e.g., 1.23.1
# Set USE_CUDA to "true" to install the GPU version, or "false" to install the CPU version
ARG ONNX_VERSION=1.23.1
ARG USE_CUDA=false

RUN if [ "$USE_CUDA" = "true" ]; then \
        echo "Installing ONNX Runtime GPU (CUDA) version ${ONNX_VERSION}"; \
        wget https://github.com/microsoft/onnxruntime/releases/download/v${ONNX_VERSION}/onnxruntime-linux-x64-gpu-${ONNX_VERSION}.tgz && \
        tar -xzf onnxruntime-linux-x64-gpu-${ONNX_VERSION}.tgz && \
        mv onnxruntime-linux-x64-gpu-${ONNX_VERSION} /usr/local/onnxruntime; \
    else \
        echo "Installing ONNX Runtime CPU version ${ONNX_VERSION}"; \
        wget https://github.com/microsoft/onnxruntime/releases/download/v${ONNX_VERSION}/onnxruntime-linux-x64-${ONNX_VERSION}.tgz && \
        tar -xzf onnxruntime-linux-x64-${ONNX_VERSION}.tgz && \
        mv onnxruntime-linux-x64-${ONNX_VERSION} /usr/local/onnxruntime; \
    fi

ENV ONNXRUNTIME_DIR=/usr/local/onnxruntime
ENV LD_LIBRARY_PATH=${ONNXRUNTIME_DIR}/lib:$LD_LIBRARY_PATH

# Set the working directory
#WORKDIR /orfs
