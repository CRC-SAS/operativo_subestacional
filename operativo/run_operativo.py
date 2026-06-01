
import os
import sys
import argparse
import datetime as dt
import logging

from calendar import Day
from pathlib import Path

from funciones_extra import descarga_pronostico, descarga_pronostico_CFSv2
from funciones_extra import get_date_for_weekday, parse_date, get_nearest_gmao_date
from funciones_extra import is_date_dayofweek, mapa_probabilidad
from prob_funciones import get_data, calc_prob, calc_prob_corr, calc_prob_corr_extr

from setup.config import  GlobalConfig
from controllers.script import ScriptControl
from errors.forecasts import FcstNotYetPublished


VALID_MODELS = ['RSMAS-CCSM4', 'NCEP-CFSv2', 'EMC-GEFSv12_CPC', 'GMAO-GEOS_V2p1', 'ECCC-GEPS8']


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description='Calibrates sub-stational forecasts.')

    parser.add_argument('modelo', type=str, choices=VALID_MODELS, help='Model to be calibrated')
    parser.add_argument('fecha', type=parse_date, help='Date to be calibrated')
    parser.add_argument('variable', type=str, choices=['pr', 'tas'], help='Variable to be calibrated (pr or tas)')
    parser.add_argument('--no-plot', dest= 'plot_maps', action='store_false', help='Don\'t generate built-in plots')
    parser.add_argument('--re-download', dest= 'redownload', action='store_true', help='Redownload input files for calibration')

    return parser.parse_args()


if __name__ == '__main__':

    # Catch and parse command-line arguments
    args: argparse.Namespace = parse_args()


    #################################
    # Inicializar script de control #
    #################################

    # Create script control
    script = ScriptControl(f'operational--{args.modelo}')

    # Start script execution
    script.start_script()


    #####################
    # Controles previos #
    #####################

    # Como la fecha guía es miércoles, pero el modelo ECCC-GEPS8 se publica los jueves, por lo tanto,
    # el script solo puede ejecutarse los viernes. A continuación se verifica que esto se cumpla:
    if not is_date_dayofweek(args.fecha, Day.FRIDAY):
        # Reportar la situación
        logging.error('El script se ejecutó un día diferente al viernes.')
        # Detener script adecuadamente (gracefully)
        script.end_script_execution()
        # Terminar ejecución
        raise SystemExit(0)


    ###################
    # Datos iniciales #
    ###################

    # Leer archivo de configuración
    config = GlobalConfig.Instance().app_config

    # Definir variables de configuración a ser utilizadas
    carpeta_datos = os.fspath(Path(f'{config.carpeta_datos}/operativo/'))
    carpeta_figuras = os.fspath(Path(f'{config.carpeta_figuras}/{args.variable}/'))
    corregir = config.corregir

    # Reportar condiciones iniciales
    logging.info('#####################################################')
    logging.info('######## Elaboración de pronóstico operativo ########')
    logging.info('#####################################################')
    logging.info(f'######## Fecha inicio de pronóstico: {args.fecha}')
    logging.info(f'######## Variable de pronóstico: {getattr(config.desc_variables, args.variable)}')
    logging.info(f'######## Se elaboran figuras con pronóstico {'corregido' if corregir else 'SIN corregir'}')
    logging.info('#####################################################')


    #####################
    # Descarga de datos #
    #####################

    # Fecha 0 siempre es el miércoles guía.
    miercoles = get_date_for_weekday(start_date=args.fecha, target_weekday=Day.WEDNESDAY)  # ---> miércoles previo

    # La fecha de publicación varía según el modelo
    match args.modelo:
        case 'RSMAS-CCSM4':
            # CCSM4 se publica los domingos, asi que se busca el domingo previo al miércoles.
            fecha_d = get_date_for_weekday(start_date=miercoles, target_weekday=Day.SUNDAY)  # --> domingo previo
        case 'NCEP-CFSv2':
            fecha_d = miercoles
        case 'EMC-GEFSv12_CPC':
            fecha_d = miercoles
        case 'GMAO-GEOS_V2p1':
            fecha_d = get_nearest_gmao_date(miercoles)  # ---> fecha GMAO más cercana
        case 'ECCC-GEPS8':
            # GEPS8 se publica los jueves, asi que se busca el jueves inmediatamente posterior al miércoles guía.
            fecha_d = miercoles + dt.timedelta(days=1)  # --> jueves posterior a fecha guía
        case _:  # Default case
            raise ValueError('Se solicitó la calibración de un modelo desconocido!')

    tipo = 'forecast'
    conj, modelo = args.modelo.split('-')

    out_folder = carpeta_datos + '/forecast/' + args.variable + '/' + miercoles.strftime('%Y%m%d%H%M') + '/'
    os.makedirs(out_folder, exist_ok=True)

    try:

        match args.modelo:
            case 'NCEP-CFSv2':
                out_files = descarga_pronostico_CFSv2(fecha_d, args.variable, tipo, conj, modelo, out_folder, args.redownload)
            case _:  # Default case
                out_file = descarga_pronostico(fecha_d, args.variable, tipo, conj, modelo, out_folder, args.redownload)

    except FcstNotYetPublished as e:
        logging.error(f'{str(e)}')
        # Finalizar el script borrando PID
        script.end_script_execution()
        # Detener ejecución del script
        sys.exit(0)



    #############################
    # Cálculo de probabilidades #
    #############################

    # Percentil 20
    fcst_m, hcst_f, media_f, pctil_f, fechas_v = get_data(fecha_d, 20, miercoles, args.variable, modelo)
    p1_20, _ = calc_prob(fcst_m, hcst_f, media_f, pctil_f, int(20))
    p1_dn20 = p1_20.sel(semanas=slice(1,3))

    # Percentil 50
    fcst_m, hcst_f, media_f, pctil_f, _ = get_data(fecha_d, 50, miercoles, args.variable, modelo)
    p1_50, p2_50 = calc_prob(fcst_m, hcst_f, media_f, pctil_f, int(50))
    p1_dn50, p2_up50 = p1_50.sel(semanas=slice(1,3)), p2_50.sel(semanas=slice(1,3))

    # Percentil 80
    fcst_m, hcst_f, media_f, pctil_f, _ = get_data(fecha_d, 80, miercoles, args.variable, modelo)
    p1_80, _ = calc_prob(fcst_m, hcst_f, media_f, pctil_f, int(80))
    p1_up80 = p1_80.sel(semanas=slice(1,3))

    # Corrección de probabilidad por PAC
    p1_dn20_corr, _ = calc_prob_corr(p1_dn20, [], args.variable, modelo, '20')
    p1_dn50_corr, p2_up50_corr = calc_prob_corr(p1_dn50, p2_up50, args.variable, modelo, '50')
    p1_up80_corr, _ = calc_prob_corr(p1_up80, [], args.variable, modelo, '80')

    # Corrección de probabilidad negativas/positivas
    p1_dn20_final, p1_up80_final = calc_prob_corr_extr(p1_dn20_corr, p1_up80_corr)
    p1_dn50_final, p2_up50_final = calc_prob_corr_extr(p1_dn50_corr, p2_up50_corr)

    # Ajustar el resultado final
    p1_dn20_final = p1_dn20_final.assign_coords(S=('semanas', pd.DatetimeIndex(p1_dn20_final['S'].values)))
    p1_dn50_final = p1_dn50_final.assign_coords(S=('semanas', pd.DatetimeIndex(p1_dn50_final['S'].values)))
    p2_up50_final = p2_up50_final.assign_coords(S=('semanas', pd.DatetimeIndex(p2_up50_final['S'].values)))
    p1_up80_final = p1_up80_final.assign_coords(S=('semanas', pd.DatetimeIndex(p1_up80_final['S'].values)))


    #########################
    # Generación de archivo #
    #########################

    for percentil in ['20-', '50-', '50+', '80+']:
        fecha_str = fecha_d.strftime('%Y%m%d%H%M')
        fecha_mie = miercoles.strftime('%Y%m%d%H%M')
        c_out = carpeta_datos + '/prob/' + args.variable + '/' + fecha_mie + '/' + percentil + '/'
        n_archivo0 = c_out + args.variable + '_underpctil' + percentil[0:2] + '_' + modelo + '_' + fecha_str + '_probability.nc'
        n_archivo1 = c_out + args.variable + '_overpctil' + percentil[0:2] + '_' + modelo + '_' + fecha_str + '_probability.nc'
        logging.info(f'######## Guardando los datos en: {c_out} ###')
        os.makedirs(c_out, exist_ok=True)
        if percentil == '20-':
            p1_dn20_final.to_netcdf(n_archivo0)
        elif percentil == '50-':
            p1_dn50_final.to_netcdf(n_archivo0)
        elif percentil == '50+':
            p2_up50_final.to_netcdf(n_archivo1)
        elif percentil == '80+':
            p1_up80_final.to_netcdf(n_archivo1)


    #########################
    # Generación de figuras #
    #########################

    if args.plot_maps:
        for percentil in ['20-', '50-', '50+', '80+']:
            c_out_f = carpeta_figuras + '/' + fecha_mie + '/' + percentil + '/'
            os.makedirs(c_out_f, exist_ok=True)

            logging.info(f'######## Guardando las figuras en: {c_out_f} ###')
            # Fechas
            f1s = fechas_v
            f2s = [fechas_v[0]+dt.timedelta(days=6), fechas_v[1]+dt.timedelta(days=6), fechas_v[2]+dt.timedelta(days=13)]

            for week, f1, f2 in zip([1,2,3], f1s, f2s):
                logging.info(f'######## - Figura semana: {week}')
                if percentil == '20-':
                    mapa_probabilidad(args.variable, p1_dn20_final, percentil[0:2], week, modelo, f1, f2, c_out_f, corr=corregir)
                elif percentil == '50-':
                    mapa_probabilidad(args.variable, p1_dn50_final, percentil[0:2], week, modelo, f1, f2, c_out_f, corr=corregir)
                elif percentil == '50+':
                    mapa_probabilidad(args.variable, p2_up50_final, percentil[0:2], week, modelo, f1, f2, c_out_f, corr=corregir)
                elif percentil == '80+':
                    mapa_probabilidad(args.variable, p1_up80_final, percentil[0:2], week, modelo, f1, f2, c_out_f, corr=corregir)


    logging.info('#####################################################')
    logging.info('############ Fin de pronostico operativo ############')
    logging.info('#####################################################')


    ###############################
    # Finalizar script de control #
    ###############################

    # End script execution
    script.end_script_execution()
