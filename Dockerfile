

##########################
## Set GLOBAL arguments ##
##########################

# Set python version
ARG PYTHON_VERSION="3.13"

# Set image variant
ARG IMG_VARIANT="-slim"

# Set APP installation folder
ARG APP_HOME="/opt/pronos/operativo"

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
RUN apt-get --quiet --assume-yes update && \
    apt-get --quiet --assume-yes upgrade && \
    apt-get --quiet --assume-yes --no-install-recommends install \
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
FROM python:${PYTHON_VERSION}${IMG_VARIANT} AS py_final

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Set python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS packages
RUN apt-get --quiet --assume-yes update && \
    apt-get --quiet --assume-yes upgrade && \
    rm -rf /var/lib/apt/lists/*

# Install python dependencies from py_builder
COPY --from=py_builder /usr/src/app/wheels /wheels
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache /wheels/* && \
    rm -rf /wheels



##########################################
## Stage 3: Install management packages ##
##########################################

# Create image
FROM py_final AS base_image

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Install OS packages
RUN apt-get --quiet --assume-yes update && \
    apt-get --quiet --assume-yes --no-install-recommends install \
        # install Tini (https://github.com/krallin/tini#using-tini)
        tini \
        # to see process with pid 1
        htop procps \
        # to allow edit files
        vim \
        # to run process with cron
        cron && \
    rm -rf /var/lib/apt/lists/*

# Create utils directory
RUN mkdir -p /opt/utils

# Create script to load environment variables
RUN printf "#!/bin/bash \n\
export \$(cat /proc/1/environ | tr '\0' '\n' | xargs -0 -I {} echo \"{}\") \n\
\n" > /opt/utils/load-envvars

# Create startup/entrypoint script
RUN printf "#!/bin/bash \n\
set -e \n\
\043 https://docs.docker.com/reference/dockerfile/#entrypoint \n\
exec \"\$@\" \n\
\n" > /opt/utils/entrypoint

# Create script to check the container's health
RUN printf "#!/bin/bash \n\
exit 0 \n\
\n" > /opt/utils/check-healthy

# Set minimal permissions to the utils scripts
RUN chmod --recursive u=rx,g=rx,o=rx /opt/utils

# Allows utils scripts to run as a non-root user
RUN chmod u+s /opt/utils/load-envvars

# Setup cron to allow it to run as a non-root user
RUN chmod u+s $(which cron)

# Add Tini (https://github.com/krallin/tini#using-tini)
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]



####################################
## Stage 4: Create APP core image ##
####################################

# Create image
FROM base_image AS app_builder

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Install OS packages
RUN apt-get --quiet --assume-yes update && \
    apt-get --quiet --assume-yes --no-install-recommends install \
        # to save scripts PID
        # to check container health
        redis-tools && \
    rm -rf /var/lib/apt/lists/*

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
RUN mkdir -p ${APP_DATA}/datos/clim/precip \
 && mkdir -p ${APP_DATA}/datos/clim/rain \
 && mkdir -p ${APP_DATA}/datos/clim/tmean \
 && mkdir -p ${APP_DATA}/datos/hindcast \
 && mkdir -p ${APP_DATA}/datos/operativo/forecast \
 && mkdir -p ${APP_DATA}/datos/operativo/prob \
 && mkdir -p ${APP_DATA}/datos/PAC/pr/CCSM4 \
 && mkdir -p ${APP_DATA}/datos/PAC/pr/CFSv2 \
 && mkdir -p ${APP_DATA}/datos/PAC/pr/GEFSv12_CPC \
 && mkdir -p ${APP_DATA}/datos/PAC/pr/GEOS_V2p1 \
 && mkdir -p ${APP_DATA}/datos/PAC/pr/GEPS8 \
 && mkdir -p ${APP_DATA}/datos/PAC/tas/CCSM4 \
 && mkdir -p ${APP_DATA}/datos/PAC/tas/CFSv2 \
 && mkdir -p ${APP_DATA}/datos/PAC/tas/GEFSv12_CPC \
 && mkdir -p ${APP_DATA}/datos/PAC/tas/GEOS_V2p1 \
 && mkdir -p ${APP_DATA}/datos/PAC/tas/GEPS8 \
 && mkdir -p ${APP_DATA}/figuras/operativo

# Save Git commit hash of this build into ${APP_HOME}/repo_version.
# https://github.com/docker/hub-feedback/issues/600#issuecomment-475941394
# https://docs.docker.com/build/building/context/#keep-git-directory
COPY ./.git /tmp/git
RUN export head=$(cat /tmp/git/HEAD | cut -d' ' -f2) && \
    if echo "${head}" | grep -q "refs/heads"; then \
    export hash=$(cat /tmp/git/${head}); else export hash=${head}; fi && \
    echo "${hash}" > ${APP_HOME}/repo_version && rm -rf /tmp/git

# Set minimum required file permissions
RUN chmod -R u=rw,g=r,o=r ${APP_HOME} \
 && chmod -R u=rw,g=r,o=r ${APP_DATA}



###################################
## Stage 5: Setup APP core image ##
###################################

# Create image
FROM app_builder AS app_core

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Renew ARGs
ARG APP_HOME
ARG APP_DATA

# Create CRON configuration file
RUN printf "\n\
SHELL=/bin/bash \n\
BASH_ENV=/opt/utils/load-envvars \n\
\n\
\043 Setup cron \n\
00 0 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py RSMAS-CCSM4 \$(date +\\%%Y-\\%%m-\\%%d) pr >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
30 0 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py RSMAS-CCSM4 \$(date +\\%%Y-\\%%m-\\%%d) tas >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
00 2 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py NCEP-CFSv2 \$(date +\\%%Y-\\%%m-\\%%d) pr >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
30 2 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py NCEP-CFSv2 \$(date +\\%%Y-\\%%m-\\%%d) tas >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
00 4 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py EMC-GEFSv12_CPC \$(date +\\%%Y-\\%%m-\\%%d) pr >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
30 4 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py EMC-GEFSv12_CPC \$(date +\\%%Y-\\%%m-\\%%d) tas >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
00 6 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py GMAO-GEOS_V2p1 \$(date +\\%%Y-\\%%m-\\%%d) pr >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
30 6 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py GMAO-GEOS_V2p1 \$(date +\\%%Y-\\%%m-\\%%d) tas >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
00 8 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py ECCC-GEPS8 \$(date +\\%%Y-\\%%m-\\%%d) pr >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
30 8 * * 5  cd ${APP_HOME}; python run_operativo_20-80.py ECCC-GEPS8 \$(date +\\%%Y-\\%%m-\\%%d) tas >> /proc/1/fd/1 2>> /proc/1/fd/1 \n\
\n" > ${APP_HOME}/crontab.conf

# Create script to check the container's health
RUN printf "#!/bin/bash \n\
readonly TRGT='operational' \n\
if [ \$(find ${APP_HOME} -type f -name '*.pid' 2>/dev/null | wc -l) != 0 ] || \n\
   [ \$(echo 'KEYS *' | redis-cli -h \${REDIS_HOST} 2>/dev/null | grep -c ${TRGT}) != 0 ] && \n\
   [ \$(ps -ef | grep -v 'grep' | grep -c 'python') == 0 ] \n\
then \n\
  exit 1 \n\
else \n\
  exit 0 \n\
fi \n\
\n" > /opt/utils/check-healthy

# Set minimal permissions to the new scripts and files
RUN chmod u=rw,g=r,o=r ${APP_HOME}/crontab.conf

# Set read-only environment variables
ENV APP_HOME=${APP_HOME}
ENV APP_DATA=${APP_DATA}

# Set user-definable environment variables
ENV CARPETA_DATOS=${APP_DATA}/datos
ENV CARPETA_FIGURAS=${APP_DATA}/figuras/operativo

# Declare optional environment variables
ENV REDIS_HOST=localhost



########################################
## Stage 6: Setup CRC-SAS final image ##
########################################

# Create image
FROM app_core AS app-root

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive

# Renew ARGs
ARG APP_HOME

# Setup CRON for root user
RUN (cat ${APP_HOME}/crontab.conf) | crontab -

# Create standard directories used for specific types of user-specific data, as defined 
# by the XDG Base Directory Specification. For when "docker run --user uid:gid" is used.
# OBS: don't forget to add --env HOME=/home when running the container.
RUN mkdir -p /home/.local/share && \
    mkdir -p /home/.cache && \
    mkdir -p /home/.config
# Set permissions, for when "docker run --user uid:gid" is used
RUN chmod -R a+rwx /home/.local /home/.cache /home/.config

# Add Tini (https://github.com/krallin/tini#using-tini)
ENTRYPOINT [ "/usr/bin/tini", "-g", "--", "/opt/utils/entrypoint" ]

# Run your program under Tini (https://github.com/krallin/tini#using-tini)
CMD [ "cron", "-fL", "15" ]
# or docker run your-image /your/program ...

# Configurar verificación de la salud del contenedor
HEALTHCHECK --interval=3s --timeout=3s --retries=3 CMD bash /opt/utils/check-healthy

# Set work directory
WORKDIR ${APP_HOME}



#####################################################
## Usage: Commands to Build and Run this container ##
#####################################################


# CONSTRUIR IMAGEN (CORE)
# docker build --pull \
#   --tag ghcr.io/crc-sas/operativo_subestacional:core-v1.0 \
#   --file Dockerfile .

# PUBLICAR IMAGEN (CORE)
# docker push ghcr.io/crc-sas/operativo_subestacional:core-v1.0

# CORRER MANUALMENTE (CRONTAB)
# docker run --rm \
#   --name prono-subestacional-rm \
#   --tty --interactive ghcr.io/crc-sas/operativo_subestacional:core-v1.0 crontab -l

# CORRER MANUALMENTE (CALIBRACIÓN - NO FUNCIONA SIN REDIS, POR PERMISOS DE ESCRITURA EN APP_HOME)
# docker run --rm \
#   --name prono-subestacional \
#   --mount type=bind,source=$(pwd)/datos,target=/opt/pronos/datos \
#   --mount type=bind,source=$(pwd)/figuras,target=/opt/pronos/figuras \
#   --user $(stat -c "%u" .):$(stat -c "%g" .) --env HOME=/home \
#   --network my-redis-network --env REDIS_HOST=my-redis-container \
#   --tty --interactive ghcr.io/crc-sas/operativo_subestacional:core-v1.0 \
#   python run_operativo_20-80.py RSMAS-CCSM4 20250101 pr

# CORRER OPERATIVAMENTE (CALIBRACIÓN - NO FUNCIONA SI NO SE CREA UN USUARIO)
# docker run --rm \
#   --name prono-subestacional \
#   --mount type=bind,source=$(pwd)/datos,target=/opt/pronos/datos \
#   --mount type=bind,source=$(pwd)/figuras,target=/opt/pronos/figuras \
#   --user $(stat -c "%u" .):$(stat -c "%g" .) --env HOME=/home \
#   --network my-redis-network --env REDIS_HOST=my-redis-container \
#   --detach ghcr.io/crc-sas/operativo_subestacional:core-v1.0
