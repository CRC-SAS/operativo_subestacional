import os
import sys
import datetime as dt
import numpy as np
from funciones_extra import descarga_pronostico
from prob_funciones import get_prono_data
# Datos iniciales para correr

fecha = sys.argv[1]
variable = sys.argv[2]
#percentil = sys.argv[3]
carpeta_dato = '../datos/operativo/'
carpeta_figuras = '../figuras/operativo/' + variable + '/'

print('#####################################################')
print('######## Elaboracion de pronostico operativo ########')
print('######## Fecha inicio de pronostico:', fecha, '####')
print('######## Variable de pronostico:', variable, '####')

#####################
# Descarga del dato
#####################
fecha_d = dt.datetime.strptime(fecha, '%Y%m%d')
tipo='forecast'; conj='EMC'; modelo='GEFSv12_CPC'
outfolder = carpeta_dato + 'forecast/' + variable + '/'
os.makedirs(outfolder, exist_ok=True)
outfile = descarga_pronostico(fecha_d, variable, tipo, conj, modelo, outfolder)
if os.stat(outfile).st_size > 10542000:
    print('Trabajando con el archivo:', outfile)

#########################
# Calculo de media
#########################
fcst_m, fechas_o, fechas_v = get_prono_data(outfile, variable, fecha_d)
