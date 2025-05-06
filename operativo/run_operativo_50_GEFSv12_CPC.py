import os
import sys
import datetime as dt
import numpy as np
from funciones_extra import descarga_pronostico, mapa_probabilidad
from prob_funciones import get_data, calc_prob, calc_prob_corr, calc_prob_corr_extr
import matplotlib.pyplot as plt
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
#print('######## Percentil de pronostico:', percentil, '####')

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
# Calculo de probabilidades
#########################
# Percentil 50+
fcst_m, hcst_f, media_f, pctil_f, fechas_v = get_data(fecha_d, 50, variable, modelo)
p1, p2 = calc_prob(fcst_m, hcst_f, media_f, pctil_f, int(50))
p_down50 = p1.sel(semanas=slice(1,3))
p_up50 = p2.sel(semanas=slice(1,3))

# Correcion de probabilidad por PAC
p_down50_corr, p_up50_corr = calc_prob_corr(p_down50, p_up50, variable, modelo, '50')
#
print(np.min(p_down50_corr.to_numpy()), np.mean(p_down50_corr.to_numpy()), np.max(p_down50_corr.to_numpy()))
print(np.min(p_up50_corr.to_numpy()), np.mean(p_up50_corr.to_numpy()), np.max(p_up50_corr.to_numpy()))

# Correcion de probabilidad negativas/positivas
p_down50_final, p_up50_final = calc_prob_corr_extr(p_down50_corr, p_up50_corr)
#
print(np.min(p_down50_final.to_numpy()), np.mean(p_down50_final.to_numpy()), np.max(p_down50_final.to_numpy()))
print(np.min(p_up50_final.to_numpy()), np.mean(p_up50_final.to_numpy()), np.max(p_up50_final.to_numpy()))

#########################
# Generacion de archivo
#########################
for percentil in ['50-', '50+']:
    fecha_str = fecha_d.strftime('%Y%m%d%H%M')
    c_out = carpeta_dato + 'prob/' + variable + '/' + percentil + '/'
    n_archivo0 = c_out + variable + '_underpctil' + percentil[0:2] + '_' + modelo + '_' + fecha_str + '_probability.nc'
    n_archivo1 = c_out + variable + '_overpctil' + percentil[0:2] + '_' + modelo + '_' + fecha_str + '_probability.nc'
    print('######## Guardando los datos en:', c_out, '###')
    os.makedirs(c_out, exist_ok=True)
    p_down50_corr.to_netcdf(n_archivo0)
    p_up50_corr.to_netcdf(n_archivo1)
    ###########################
    # Generacion de figuras
    ###########################
    c_out_f = carpeta_figuras + fecha_str + '/' + percentil + '/'
    os.makedirs(c_out_f, exist_ok=True)

    print('######## Guardando las figuras en:', c_out_f, '###')
    # Fechas
    f1s = fechas_v
    f2s = [fechas_v[0]+dt.timedelta(days=6), fechas_v[1]+dt.timedelta(days=6), fechas_v[2]+dt.timedelta(days=13)]

    for week, f1, f2 in zip([1,2,3], f1s, f2s):
        print('######### Figura semana:', week)
        if percentil == '50-':
            mapa_probabilidad(variable, p_down50_final, percentil, week, f1, f2, c_out_f, corr=True)
            mapa_probabilidad(variable, p_down50, percentil, week, f1, f2, c_out_f, corr=False)
        elif percentil == '50+':
            mapa_probabilidad(variable, p_up50_final, percentil, week, f1, f2, c_out_f, corr=True)
            mapa_probabilidad(variable, p_up50, percentil, week, f1, f2, c_out_f, corr=False)
        

print('############ Fin de pronostico operativo ############')
print('#####################################################')