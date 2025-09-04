#!/usr/bin/env bash

docker volume create \
    --driver local \
    --opt type=none \
    --opt device=/mnt/hdd-1/ReposGIT/operativo_subestacional/datos \
    --opt o=bind \
    --name pronos-subestacionales-datos-1 \
    --label description="Datos de entrada para la calibración de pronósticos subestacionales"

docker volume create \
    --driver local \
    --opt type=none \
    --opt device=/mnt/hdd-1/ReposGIT/operativo_subestacional/figuras \
    --opt o=bind \
    --name pronos-subestacionales-figuras-1 \
    --label description="Gráficos generados por la calibración de pronósticos subestacionales"
