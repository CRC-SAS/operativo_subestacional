
##########################
## Set GLOBAL arguments ##
##########################

# Set python version
ARG PYTHON_VERSION="3.13"

# Set image variant
ARG IMG_VARIANT="-slim"

# Set APP installation folder
ARG APP_HOME="/opt/pronos/scripts"

# Set APP data folder
ARG APP_DATA="/opt/pronos"



######################################
## Stage 1: Install Python packages ##
######################################

# Create image
FROM python:${PYTHON_VERSION}${IMG_VARIANT} AS py_builder

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Set python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS packages
RUN apt-get -y -qq update && \
    apt-get -y -qq upgrade && \
    apt-get -y -qq --no-install-recommends install \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /usr/src/app

# Upgrade pip and install dependencies
RUN python3 -m pip install --upgrade pip
# Copy dependencies from build context
COPY requirements.txt requirements.txt
# Install Python dependencies (ver: https://stackoverflow.com/a/17311033/5076110)
RUN python3 -m pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt



###############################################
## Stage 2: Copy Python installation folders ##
###############################################

# Create image
FROM python:${PYTHON_VERSION}${IMG_VARIANT} AS py_core

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Install python dependencies from py_builder
COPY --from=py_builder /usr/src/app/wheels /wheels
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache /wheels/* && \
    rm -rf /wheels



###########################################
## Stage 4: Install management packages  ##
###########################################

# Create image
FROM py_core AS py_final

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Install OS packages
RUN apt-get -y -qq update && \
    apt-get -y -qq --no-install-recommends install \
        # install Tini (https://github.com/krallin/tini#using-tini)
        tini \
        # to see process with pid 1
        htop procps \
        # to allow edit files
        vim \
        # to run process with cron
        cron && \
    rm -rf /var/lib/apt/lists/*

# Setup cron to allow it run as a non root user
RUN chmod u+s $(which cron)

# Add Tini (https://github.com/krallin/tini#using-tini)
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]



####################################
## Stage 3: Create APP core image ##
####################################

# Create image
FROM py_final AS app_builder

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Renew ARGs
ARG APP_HOME
ARG APP_DATA

# Create APP_HOME folder
RUN mkdir -p ${APP_HOME}

# Copy project
COPY ./operativo/ ${APP_HOME}

# Create APP_DATA folder
RUN mkdir -p ${APP_DATA}

# Create data folders
RUN mkdir -p ${APP_DATA}/datos/clim/precip
RUN mkdir -p ${APP_DATA}/datos/clim/tmean
RUN mkdir -p ${APP_DATA}/datos/hindcast
RUN mkdir -p ${APP_DATA}/datos/PAC/pr/CCSM4
RUN mkdir -p ${APP_DATA}/datos/PAC/pr/CFSv2
RUN mkdir -p ${APP_DATA}/datos/PAC/pr/GEFSv12_CPC
RUN mkdir -p ${APP_DATA}/datos/PAC/pr/GEOS_V2p1
RUN mkdir -p ${APP_DATA}/datos/PAC/pr/GEPS8
RUN mkdir -p ${APP_DATA}/datos/PAC/tas/CCSM4
RUN mkdir -p ${APP_DATA}/datos/PAC/tas/CFSv2
RUN mkdir -p ${APP_DATA}/datos/PAC/tas/GEFSv12_CPC
RUN mkdir -p ${APP_DATA}/datos/PAC/tas/GEOS_V2p1
RUN mkdir -p ${APP_DATA}/datos/PAC/tas/GEPS8
RUN mkdir -p ${APP_DATA}/figuras/operativo

# Crear archivo datos_entrada.txt
RUN printf "\n\
carpeta_datos = \"${APP_DATA}/datos/\" \n\
carpeta_figuras = \"${APP_DATA}/figuras/operativo/\" \n\
corregir = \"True\" \n\
\n" > ${APP_HOME}/datos_entrada.txt
RUN chmod a+rw ${APP_HOME}/datos_entrada.txt

# Crear archivo de configuración de CRON
RUN printf "\n\
SHELL=/bin/bash \n\
\n\
\043 Setup cron \n\
* * * * *  /bin/echo 'Fecha y hora: \$(date)' >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
\n" > ${APP_HOME}/crontab.txt
RUN chmod a+rw ${APP_HOME}/crontab.txt

# Save Git commit hash of this build into ${APP_HOME}/repo_version.
# https://github.com/docker/hub-feedback/issues/600#issuecomment-475941394
# https://docs.docker.com/build/building/context/#keep-git-directory
COPY ./.git /tmp/git
RUN export head=$(cat /tmp/git/HEAD | cut -d' ' -f2) && \
    if echo "${head}" | grep -q "refs/heads"; then \
    export hash=$(cat /tmp/git/${head}); else export hash=${head}; fi && \
    echo "${hash}" > ${APP_HOME}/repo_version && rm -rf /tmp/git

# Set permissions of app files
RUN chmod -R ug+rw,o+r,o-w ${APP_HOME}

# Set read-only environment variables
ENV APP_HOME=${APP_HOME}
ENV APP_DATA=${APP_DATA}



####################################
## Stage 4: Setup APP core image  ##
####################################

# Create image
FROM app_builder AS app-core

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Renew ARGs
ARG APP_HOME

# Setup CRON for root user
RUN (cat ${APP_HOME}/crontab.txt) | crontab -

# Create standard directories used for specific types of user-specific data, as defined 
# by the XDG Base Directory Specification. For when "docker run --user uid:gid" is used.
# OBS: don't forget to add --env HOME=/home when running the container.
RUN mkdir -p /home/.local/share && \
    mkdir -p /home/.cache && \
    mkdir -p /home/.config
# Set permissions, for when "docker run --user uid:gid" is used
RUN chmod -R a+rwx /home/.local /home/.cache /home/.config

# Add Tini (https://github.com/krallin/tini#using-tini)
ENTRYPOINT [ "/usr/bin/tini", "-g", "--" ]

# Run your program under Tini (https://github.com/krallin/tini#using-tini)
CMD [ "python", "--version" ]
# or docker run your-image /your/program ...

# Set work directory
WORKDIR ${APP_HOME}



#####################################################
## Usage: Commands to Build and Run this container ##
#####################################################


# CONSTRUIR IMAGEN (CORE)
# docker build --pull \
#   --tag prono-subestacional:latest \
#   --file Dockerfile .

# CORRER MANUALMENTE
# docker run --rm \
#   --name prono-subestacional \
#   --mount type=bind,source=$(pwd)/datos,target=/opt/pronos/datos \
#   --mount type=bind,source=$(pwd)/figuras,target=/opt/pronos/figuras \
#   --user $(stat -c "%u" .):$(stat -c "%g" .) --env HOME=/home \
#   --workdir /opt/pronos/scripts \
#   --tty --interactive prono-subestacional:latest \
#   python /opt/pronos/scripts/run_operativo_20-80_GEPS8.py 20250101 pr

# CONSTRUIR IMAGEN (NON-ROOT)
# docker build \
#   --tag prono-subestacional:nonroot \
#   --build-arg BASE_IMAGE="prono-subestacional:latest" \
#   --build-arg USER_UID=$(stat -c "%u" .) \
#   --build-arg USER_GID=$(stat -c "%g" .) \
#   --file Dockerfile.nonroot .

# CORRER MANUALMENTE
# docker run --rm \
#   --name prono-subestacional \
#   --mount type=bind,source=$(pwd)/datos,target=/opt/pronos/datos \
#   --mount type=bind,source=$(pwd)/figuras,target=/opt/pronos/figuras \
#   --user $(stat -c "%u" .):$(stat -c "%g" .) \
#   --workdir /opt/pronos/scripts \
#   --tty --interactive prono-subestacional:nonroot \
#   python /opt/pronos/scripts/run_operativo_20-80_GEPS8.py 20250101 pr

# CORRER OPERATIVAMENTE
# docker run --rm \
#   --name prono-subestacional \
#   --mount type=bind,source=$(pwd)/datos,target=/opt/pronos/datos \
#   --mount type=bind,source=$(pwd)/figuras,target=/opt/pronos/figuras \
#   --user $(stat -c "%u" .):$(stat -c "%g" .) \
#   --workdir /opt/pronos/scripts \
#   --detach prono-subestacional:nonroot