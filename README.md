# Calibración Operativa de Pronósticos Subestacionales
Este proyecto reúne el código nacesario para ejecutar calibraciones operativas de pronósticos subestacionales. 
Es un proyecto que forma parte de un proyecto mayor denominado ENANDES+.

## Calibración de pronósticos

La versión actual permite calibrar pronósticos de cinco fuentes diferentes: RSMAS-CCSM4, NCEP-CFSv2, 
EMC-GEFSv12_CPC, GMAO-GEOS_V2p1, ECCC-GEPS8. Anteriormente, cada uno de estos modelos se calibraban mediante
la ejecución de un script diferente, sin embargo, la versión actual permite calibrarlos todos mediante un único 
script: run_operativo_20-80.py.


### Ejemplos de uso

- Para acceder a la ayuda del script ejecutar el siguiente comando:
```commandline
python run_operativo_20-80.py --help
```
- Para calibrar pronósticos RSMAS-CCSM4 ejecutar el siguiente comando:
```commandline
python run_operativo_20-80.py RSMAS-CCSM4 2025-08-27 pr
```
- Para calibrar pronósticos NCEP-CFSv2 ejecutar el siguiente comando:
```commandline
python run_operativo_20-80.py NCEP-CFSv2 2025-08-27 pr
```
- Para calibrar pronósticos EMC-GEFSv12_CPC ejecutar el siguiente comando:
```commandline
python run_operativo_20-80.py EMC-GEFSv12_CPC 2025-08-27 pr
```
- Para calibrar pronósticos GMAO-GEOS_V2p1 ejecutar el siguiente comando:
```commandline
python run_operativo_20-80.py GMAO-GEOS_V2p1 2025-08-27 pr
```
- Para calibrar pronósticos ECCC-GEPS8 ejecutar el siguiente comando:
```commandline
python run_operativo_20-80.py ECCC-GEPS8 2025-08-27 pr
```
