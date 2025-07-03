import os
import sys
import datetime as dt
import numpy as np
from funciones_extra import descarga_pronostico_CFSv2, mapa_probabilidad
from prob_funciones import get_data, calc_prob, calc_prob_corr, calc_prob_corr_extr
from funciones_extra import parse_config, str_to_bool


fecha = sys.argv[1]
variable = sys.argv[2]
#percentil = sys.argv[3]
# Archivo con carpetas
config_file = 'datos_entrada.txt'
# Leemos el archivo
config = parse_config(config_file)
carpeta = config.get('carpeta_datos')
carpeta_dato = carpeta + 'operativo/'
carpeta_figuras = config.get('carpeta_figuras') + variable + '/'
corregir = str_to_bool(config.get('corregir'))

nombre_var = {'pr': 'Acumulado semanal de lluvia', 
              'tas': 'Temperatura media de la semana'}

print('#####################################################')
print('######## Elaboracion de pronostico operativo ########')
print('######## Fecha inicio de pronostico:', fecha, '####')
print('######## Variable de pronostico:', nombre_var[variable], '####')
if corregir:
    print(u'######## Se elaboran figuras con pronóstico corregido ####')
else:
    print(u'######## Se elaboran figuras con pronóstico SIN corregir ####')

#####################
# Descarga del dato
#####################
miercoles = dt.datetime.strptime(fecha, '%Y%m%d')
fecha_d = miercoles
tipo='forecast'; conj='NCEP'; modelo='CFSv2'
outfolder = carpeta_dato + 'forecast/' + variable + '/' + miercoles.strftime('%Y%m%d%H%M') + '/'
os.makedirs(outfolder, exist_ok=True)
outfiles = descarga_pronostico_CFSv2(fecha_d, variable,  outfolder)
if len(outfiles) > 1:
    print('Trabajando con los archivos:', outfiles)

#########################
# Calculo de probabilidades
#########################
# Percentil 20
fcst_m, hcst_f, media_f, pctil_f, fechas_v = get_data(fecha_d, 20, fecha_d, variable, modelo)
p1, p2 = calc_prob(fcst_m, hcst_f, media_f, pctil_f, int(20))
p1_20 = p1.sel(semanas=slice(1,3))

# Percentil 80
fcst_m, hcst_f, media_f, pctil_f, fechas_v = get_data(fecha_d, 80, fecha_d, variable, modelo)
p1, p2 = calc_prob(fcst_m, hcst_f, media_f, pctil_f, int(80))
p1_80 = p1.sel(semanas=slice(1,3))

# Correcion de probabilidad por PAC
p1_20_corr, p2_corr = calc_prob_corr(p1_20, p2, variable, modelo, '20')
p1_80_corr, p2_corr = calc_prob_corr(p1_80, p2, variable, modelo, '80')

# Correcion de probabilidad negativas/positivas
p1_20_final, p1_80_final = calc_prob_corr_extr(p1_20_corr, p1_80_corr)

#########################
# Generacion de archivo
#########################
for percentil in ['20', '80']:
    fecha_str = fecha_d.strftime('%Y%m%d%H%M')
    fecha_mie = miercoles.strftime('%Y%m%d%H%M')
    c_out = carpeta_dato + 'prob/' + variable + '/' + fecha_mie + '/' + percentil + '/'
    n_archivo0 = c_out + variable + '_underpctil' + percentil + '_' + modelo + '_' + fecha_str + '_probability.nc'
    n_archivo1 = c_out + variable + '_overpctil' + percentil + '_' + modelo + '_' + fecha_str + '_probability.nc'
    print('######## Guardando los datos en:', c_out, '###')
    os.makedirs(c_out, exist_ok=True)
    if percentil == '20':
        p1_20_final.to_netcdf(n_archivo0)
    elif percentil == '80':
        p1_80_final.to_netcdf(n_archivo1)
    else:
        p1.to_netcdf(n_archivo0)
        p2.to_netcdf(n_archivo1)
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
        if percentil == '20':
            mapa_probabilidad(variable, p1_20_final, percentil, week, modelo, f1, f2, c_out_f, corr=corregir)
            #mapa_probabilidad(variable, p1_20, percentil, week, modelo, f1, f2, c_out_f, corr=False)
        elif percentil == '80':
            mapa_probabilidad(variable, p1_80_final, percentil, week, modelo, f1, f2, c_out_f, corr=corregir)
            #mapa_probabilidad(variable, p1_80, percentil, week, modelo, f1, f2, c_out_f, corr=False)
        

print('############ Fin de pronostico operativo ############')
print('#####################################################')