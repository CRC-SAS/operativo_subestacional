
import os
import argparse
import datetime as dt

from calendar import Day
from pathlib import Path

from funciones_extra import descarga_pronostico_CFSv2, mapa_probabilidad
from prob_funciones import get_data, calc_prob, calc_prob_corr, calc_prob_corr_extr
from funciones_extra import get_date_for_weekday, parse_date
from setup.config import  GlobalConfig


###############################
# Datos iniciales para correr #
###############################

# Defines parser data
parser = argparse.ArgumentParser(description='Calibrates sub-stational CFSv2 forecasts.')
parser.add_argument('fecha', type=parse_date, help='Date to be calibrated')
parser.add_argument('variable', type=str, choices=['pr', 'tas'], help='Variable to be calibrated (pr or tas)')
parser.add_argument('--no-plot', dest='plot_maps', action='store_false', help='Don\'t generate built-in plots')
args = parser.parse_args()

# Leer archivo de configuración
config = GlobalConfig.Instance().app_config
# Definir variables a ser utilizadas
carpeta_datos = os.fspath(Path(f'{config.carpeta_datos}/operativo/'))
carpeta_figuras = os.fspath(Path(f'{config.carpeta_figuras}/{args.variable}/'))
corregir = config.corregir


print('#####################################################')
print('######## Elaboración de pronóstico operativo ########')
print('#####################################################')
print(f'######## Fecha inicio de pronóstico: {args.fecha}')
print(f'######## Variable de pronóstico: {getattr(config.desc_variables, args.variable)}')
print(f'######## Se elaboran figuras con pronóstico {'corregido' if corregir else 'SIN corregir'}')
print('#####################################################')


#####################
# Descarga del dato #
#####################

# Fecha 0 siempre es el miercoles guía.
miercoles = get_date_for_weekday(start_date=args.fecha, target_weekday=Day.WEDNESDAY)  # ---> miércoles
fecha_d = miercoles

tipo='forecast'
conj='NCEP'
modelo='CFSv2'

out_folder = carpeta_datos + '/forecast/' + args.variable + '/' + miercoles.strftime('%Y%m%d%H%M') + '/'
os.makedirs(out_folder, exist_ok=True)
out_files = descarga_pronostico_CFSv2(fecha_d, args.variable,  out_folder)

if len(out_files) > 1:
    print('Trabajando con los archivos:', out_files)


#############################
# Cálculo de probabilidades #
#############################

# Percentil 20
fcst_m, hcst_f, media_f, pctil_f, fechas_v = get_data(fecha_d, 20, miercoles, args.variable, modelo)
p1, p2 = calc_prob(fcst_m, hcst_f, media_f, pctil_f, int(20))
p1_20 = p1.sel(semanas=slice(1,3))

# Percentil 80
fcst_m, hcst_f, media_f, pctil_f, _ = get_data(fecha_d, 80, miercoles, args.variable, modelo)
p1, _ = calc_prob(fcst_m, hcst_f, media_f, pctil_f, int(80))
p1_80 = p1.sel(semanas=slice(1,3))

# Corrección de probabilidad por PAC
p1_20_corr, p2_20_corr = calc_prob_corr(p1_20, p2, args.variable, modelo, '20')
p1_80_corr, p2_80_corr = calc_prob_corr(p1_80, p2, args.variable, modelo, '80')

# Corrección de probabilidad negativas/positivas
p1_20_final, p1_80_final = calc_prob_corr_extr(p1_20_corr, p1_80_corr)


#########################
# Generación de archivo #
#########################

for percentil in ['20', '80']:
    fecha_str = fecha_d.strftime('%Y%m%d%H%M')
    fecha_mie = miercoles.strftime('%Y%m%d%H%M')
    c_out = carpeta_datos + '/prob/' + args.variable + '/' + fecha_mie + '/' + percentil + '/'
    n_archivo0 = c_out + args.variable + '_underpctil' + percentil + '_' + modelo + '_' + fecha_str + '_probability.nc'
    n_archivo1 = c_out + args.variable + '_overpctil' + percentil + '_' + modelo + '_' + fecha_str + '_probability.nc'
    print('######## Guardando los datos en:', c_out, '###')
    os.makedirs(c_out, exist_ok=True)
    if percentil == '20':
        p1_20_final.to_netcdf(n_archivo0)
    elif percentil == '80':
        p1_80_final.to_netcdf(n_archivo1)
    else:
        p1.to_netcdf(n_archivo0)
        p2.to_netcdf(n_archivo1)


#########################
# Generación de figuras #
#########################

if args.plot_maps:
    for percentil in ['20', '80']:
        c_out_f = carpeta_figuras + '/' + fecha_mie + '/' + percentil + '/'
        os.makedirs(c_out_f, exist_ok=True)

        print('######## Guardando las figuras en:', c_out_f, '###')
        # Fechas
        f1s = fechas_v
        f2s = [fechas_v[0]+dt.timedelta(days=6), fechas_v[1]+dt.timedelta(days=6), fechas_v[2]+dt.timedelta(days=13)]

        for week, f1, f2 in zip([1,2,3], f1s, f2s):
            print('######### Figura semana:', week)
            if percentil == '20':
                mapa_probabilidad(args.variable, p1_20_final, percentil, week, modelo, f1, f2, c_out_f, corr=corregir)
            elif percentil == '80':
                mapa_probabilidad(args.variable, p1_80_final, percentil, week, modelo, f1, f2, c_out_f, corr=corregir)


print('############ Fin de pronostico operativo ############')
print('#####################################################')
