import os
import datetime as dt
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import colors as c
import cartopy.crs as ccrs

from funciones_extra import grouping_coord, grouping_coord_fecha

def get_prono_data(archivo, variable, miercoles):
    fcst = xr.open_dataset(archivo)
    if 'tas' in list(fcst.variables):
        fcst = fcst.tas - 273.15
    else:
        fcst = fcst[variable]
    fcst, fechas = grouping_coord_fecha(fcst, miercoles, hcast=0)

    fechas_o = [dt.datetime(a.year, a.month, a.day ).replace(year=1960).replace(hour=0) for a in fechas]
    fechas_v = [a for a in fechas]
    # calculo de media semanal 1, 2, 3y4, 5
    if variable == 'tas':
        fcst_m = fcst.groupby('semanas').mean(dim='L').squeeze()
    elif variable == 'pr':
        fcst_m = fcst.groupby('semanas').sum(dim='L').squeeze()
    fcst_m = fcst_m.sel(semanas=slice(1,5))

    return fcst_m, fechas_o, fechas_v

def get_hindcast_data(archivo, variable, fecha, miercoles):
    hcst = xr.open_dataset(archivo)
    # seleccionar los datos a partir de inicio de pronóstico
    mes = fecha.month
    dia = fecha.day
    f1 = dt.datetime(1960, int(mes), int(dia))
    if 'tas' in list(hcst.variables):
        hcst = hcst.tas.sel(S=f1) - 273.15
    else:
        hcst = hcst[variable].sel(S=f1)
    hcst1, fechas = grouping_coord_fecha(hcst, miercoles, hcast=1)
    #### Ojo aca que depende de la variable. Como se trabaja con temperatura, se queda la media.
    # calculo de media semanal
    if variable == 'tas':
        hcst_m = hcst1.groupby('semanas').mean(dim='L').squeeze()
    elif variable == 'pr':
        hcst_m = hcst1.groupby('semanas').sum(dim='L').squeeze()
    
    return hcst_m

def get_media_data(archivo, variable, f1, f2, dato_o, miercoles):
    ##### Media diaria ERA5 (la de CPC andaba mal)
    # se extraen los datos de la semana
    # se extiende el año hasta el 28 de febrero.
    media0 = xr.open_dataset(archivo)
    media1 = media0.sel(S=slice('1960-01-01', '1960-02-28')).copy()
    new_time_coords = pd.date_range(start='1961-01-01', end='1961-02-28', freq='D')
    media1 = media1.assign_coords(time=('S', new_time_coords))
    media1 = media1.swap_dims({'S': 'time'})
    media1 = media1.drop('S')
    media1 = media1.rename({'time':'S'})
    #
    media = xr.concat([media0, media1], dim='S')
    media = media[variable].sel(S=slice(f1, f2))
    media = media.rename({'longitude': 'X','latitude': 'Y'})
    #    
    media1, fechas = grouping_coord_fecha(media, miercoles, hcast=2)

    if variable == 'tmean':
        media_m = media1.groupby('semanas').mean(dim='S').squeeze()
    elif variable == 'rain':
        media_m = media1.groupby('semanas').sum(dim='S').squeeze()
    # Interpolamos a la reticula de subX
    media_m_i = media_m.interp_like(dato_o)

    return media_m_i

def get_pctil_data(archivo0, archivo1, variable, fechas_o, fechas_v, dato_o):
    ##### Percentil ERA5
    # 1 valor para cada semana
    pctil1 = xr.open_dataset(archivo0)
    pctil1 = pctil1[variable]
    pctil1 = pctil1.rename({'longitude': 'X','latitude': 'Y'})
    pctil1 = pctil1.sel(S=fechas_o[0:2])
    # Interpolamos a la reticula de subX
    pctil1_i = pctil1.interp_like(dato_o)
    pctil1_i = pctil1_i.assign_coords(S=('S',fechas_v[0:2]))
    pctil1_i['S'] = pd.DatetimeIndex(pctil1_i['S'].values)
    pctil1_i = pctil1_i.assign_coords(semanas=('S', np.array([1.,2.]))).swap_dims({'S':'semanas'})
    
    # 1 valor para cada promedio de 2 semanas
    pctil2 = xr.open_dataset(archivo1)
    pctil2 = pctil2[variable]
    pctil2 = pctil2.rename({'longitude': 'X','latitude': 'Y'})
    pctil2 = pctil2.sel(S=fechas_o[2:4])
    # Interpolamos a la reticula de subX
    pctil2_i = pctil2.interp_like(dato_o)
    pctil2_i = pctil2_i.assign_coords(S=('S',fechas_v[2:4]))
    pctil2_i['S'] = pd.DatetimeIndex(pctil2_i['S'].values)
    pctil2_i = pctil2_i.assign_coords(semanas=('S', np.array([3.,5.]))).swap_dims({'S':'semanas'})

    # concatenamos valores
    pctil_i = xr.concat([pctil1_i, pctil2_i], 'semanas')
    
    return pctil_i


def get_data(fecha, pctil, miercoles, variable='tas', modelo='GEOS_V2p1'):
    carpeta = '../datos/'
    fecha_str = fecha.strftime('%Y%m%d%H%M')
    mierc_str = miercoles.strftime('%Y%m%d%H%M')
    varn = {'tas':'tmean', 'tasmin':'tmin', 'tasmax':'tmax', 'pr':'rain', 'zg':'z200'}
    nf1 = variable +'_' + modelo + '_' + fecha_str + '_forecast.nc'
    a0 = carpeta + 'operativo/forecast/' + variable + '/' + mierc_str + '/' + nf1
    a1 = carpeta + 'hindcast/' + variable +'_' + modelo + '_datos.nc'
    a2 = carpeta + 'clim/' + varn[variable] + '/' + varn[variable] + 'ClimSmooth.nc'
    a3 = carpeta + 'clim/' + varn[variable] + '/' + varn[variable] + '_weeklymean_pctile' + str(pctil) + '_smooth.nc'
    a4 = carpeta + 'clim/' + varn[variable] + '/' + varn[variable] + '_2weeklymean_pctile' + str(pctil) + '_smooth.nc'

    print('$$$$$$$$$$$$$$ DATOS UTILIZADOS $$$$$$$$$$$$$$$$$$$$$')
    print('$$$$ Archivo pronostico:', a0)
    print('$$$$ Archivo hindcast:', a1)
    print('$$$$ Archivo diario historico:', a2)
    print('$$$$ Archivo percentil 1 semana:', a3)
    print('$$$$ Archivo percentil 2 semana:', a4)
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')

    fcst_len = xr.open_dataset(a0, engine='netcdf4').sizes['L']-1
    fcst_m, fechas_o, fechas_v = get_prono_data(a0, variable, miercoles)
    f1 = fechas_o[0]
    f2 = f1 + dt.timedelta(days=fcst_len)
    
    hcst_m = get_hindcast_data(a1, variable, fechas_o[0], miercoles)
    media_m_i = get_media_data(a2, varn[variable], f1, f2, hcst_m, miercoles)
    pctil_i = get_pctil_data(a3, a4, varn[variable], fechas_o, fechas_v, hcst_m)
   
    aux_hcst = []
    aux_media = []
    aux_pctil = []
    for i in range(fcst_m.sizes['M']):
        aux_hcst.append(hcst_m)
        aux_media.append(media_m_i)
        aux_pctil.append(pctil_i)
    media_f = xr.concat(aux_media, fcst_m.M)
    pctil_f = xr.concat(aux_pctil, fcst_m.M)
    hcst_f = xr.concat(aux_hcst, fcst_m.M)

#    print(fcst_m)
#    print(hcst_f)
#    print(media_f)
#    print(pctil_f)
    print(fechas_v)

    return fcst_m, hcst_f, media_f, pctil_f, fechas_v

def calc_prob(fcst_m, hcst_f, media_f, pctil_f, pctil):

    new_fcst = fcst_m - hcst_f + media_f
   
    if pctil == 20:
        p1 = 100*(xr.where(new_fcst < pctil_f, 1., 0. ).sum(dim='M')/fcst_m.sizes['M'])
        p1 = p1.rename('prob')
        p1 = p1.assign_attrs(standard_name='Probabilidad bajo percentil 20')
        #print(np.min(p1.to_numpy()), np.mean(p1.to_numpy()), np.max(p1.to_numpy()))
        p2 = []
    elif pctil == 80:
        p1 = 100*(xr.where(new_fcst > pctil_f, 1., 0. ).sum(dim='M')/fcst_m.sizes['M'])
        p1 = p1.rename('prob')
        p1 = p1.assign_attrs(standard_name='Probabilidad sobre percentil 80')
        #print(np.min(p1.to_numpy()), np.mean(p1.to_numpy()), np.max(p1.to_numpy()))
        p2 = []
    else: # pctil = 50
        p1 = 100*(xr.where(new_fcst < pctil_f, 1., 0. ).sum(dim='M')/fcst_m.sizes['M'])
        p2 = 100*(xr.where(new_fcst > pctil_f, 1., 0. ).sum(dim='M')/fcst_m.sizes['M'])
        p1 = p1.rename('prob')
        p2 = p2.rename('prob')
        p1 = p1.assign_attrs(standard_name='Probabilidad bajo percentil 50')
        p2 = p2.assign_attrs(standard_name='Probabilidad sobre percentil 50')
        #print(np.min(p1.to_numpy()), np.mean(p1.to_numpy()), np.max(p1.to_numpy()))
        #print(np.min(p2.to_numpy()), np.mean(p2.to_numpy()), np.max(p2.to_numpy()))
    
    return p1, p2


def calc_prob_corr(p1, p2, variable, modelo, percentil):
    '''
    Se corrige la probabilidad obtenida segun el trabajo de Van de Dool et al 2017
    '''
    if str(percentil) == '20':
        cp = 0.2
    elif str(percentil) == '80':
        cp = 0.2
    else:
        cp = 0.5
    c_PAC = '../datos/PAC/' + variable + '/'
    if (percentil == '20') or (percentil == '80'):
        " Lista vacia para p2, ie el percentil es 20 o 80"
        list_corr = []
        for week in [1,2,3]:
            print('Week:', week)
            f1 = c_PAC + '/' + modelo + '/' + variable + '_PAC_semana' + str(week) + '_pctil' + str(percentil) + '.nc'
            f2 = c_PAC + '/' + modelo + '/' + variable + '_stdo_semana' + str(week) + '_pctil' + str(percentil) + '.nc'
            f3 = c_PAC + '/' + modelo + '/' + variable + '_stdp_semana' + str(week) + '_pctil' + str(percentil) + '.nc'
            print(f1, f2,f3)
            
            PAC = xr.open_dataset(f1)['PAC']
            std_o = xr.open_dataset(f2)['std_o']
            std_p = xr.open_dataset(f3)['std_p']
            corr_factor = PAC*(std_o/std_p)
            #print('Factor', corr_factor.min().values, corr_factor.max().values)
            prob = p1.sel(semanas=week)*0.01
            p_corr = xr.where(corr_factor>0, (cp  + corr_factor*(prob - cp)), cp)
            p_corr = 100.*p_corr
            p_corr = p_corr.rename('prob_corr')
            #aux = xr.where(p_corr>200, prob, np.nan).to_numpy()
            #aux0 = xr.where(p_corr>200, corr_factor, np.nan).to_numpy()
            #print(aux[~np.isnan(aux)])
            #print(aux0[~np.isnan(aux)])
            #print(cp+aux0[~np.isnan(aux)]*(aux[~np.isnan(aux)]-cp))
            list_corr.append(p_corr)
        p1_corr = xr.concat(list_corr, dim='semanas')
        print('###########################')
        return p1_corr, p1_corr
    else:
        " Hay datos en p2, ie el percentil es 50 y se calculan probabilidades por sobre y por debajo"
        list_corr1 = []
        list_corr2 = []
        for week in [1,2,3]:
            # Archivos para corregir 50-
            f1 = c_PAC + '/' + modelo + '/' + variable + '_PAC_semana' + str(week) + '_pctil50-.nc'
            f2 = c_PAC + '/' + modelo + '/' + variable + '_stdo_semana' + str(week) + '_pctil50-.nc'
            f3 = c_PAC + '/' + modelo + '/' + variable + '_stdp_semana' + str(week) + '_pctil50-.nc'
            print(f1, f2,f3)
            # ################
            # para 50-
            PAC = xr.open_dataset(f1)['PAC']
            std_o = xr.open_dataset(f2)['std_o']
            std_p = xr.open_dataset(f3)['std_p']
            corr_factor = PAC*(std_o/std_p)
            prob = p1.sel(semanas=week)*0.01
            p_corr1 = xr.where(corr_factor>0, (cp  + corr_factor*(prob - cp)), cp)
            p_corr1 = 100.*p_corr1
            p_corr1 = p_corr1.rename('prob_corr')
            ############################################
            # Archivos para corregir 50+
            f1 = c_PAC + '/' + modelo + '/' + variable + '_PAC_semana' + str(week) + '_pctil50+.nc'
            f2 = c_PAC + '/' + modelo + '/' + variable + '_stdo_semana' + str(week) + '_pctil50+.nc'
            f3 = c_PAC + '/' + modelo + '/' + variable + '_stdp_semana' + str(week) + '_pctil50+.nc'
            print(f1, f2,f3)
            # ################
            # para 50+
            PAC = xr.open_dataset(f1)['PAC']
            std_o = xr.open_dataset(f2)['std_o']
            std_p = xr.open_dataset(f3)['std_p']
            corr_factor = PAC*(std_o/std_p)
            prob = p2.sel(semanas=week)*0.01
            p_corr2 = xr.where(corr_factor>0, (cp  + corr_factor*(prob - cp)), cp)
            p_corr2 = 100.*p_corr2
            p_corr2 = p_corr2.rename('prob_corr')
            #print(p_corr.min().values, p_corr.mean().values, p_corr.max().values)
            list_corr1.append(p_corr1)
            list_corr2.append(p_corr2)
        p1_corr = xr.concat(list_corr1, dim='semanas')
        p2_corr = xr.concat(list_corr2, dim='semanas')
        print('###########################')
        return p1_corr, p2_corr


def calc_prob_corr_extr(p1, p2):
    '''
    Se corrige la probabilidad obtenida segun el trabajo de Van de Dool et al 2017
    p1 --> percentil 20
    p2 --> percentil 80
    Las "tres clases" en este ejercicio, siguiendo el paper son:
    p1-> Probabilidad bajo percentil 20
    p_no -> Probabilidad entre percentil 20 y 80
    p2-> Probabilidad sobre percentil 80

    En este caso, el valor de p_no no se considera.
    '''
    iter = 3
    p1_o = p1.copy()
    p2_o = p2.copy()
    ##################################################
    #Se trabaja con prob percentil 20
    negativo = bool((p1 < 0).any().to_numpy().any())
    i = 1
    if negativo:
        print('Hay valores bajo 0 para percentil 20, corregimos')
        while i<=iter:
            discrepancy = xr.where(p1<0, p1-1, 0)
            #sumamos la mitad a donde corresponda
            p2_o = p2 + 0.5*discrepancy
            p1_o = p1_o.where(p1>=0, 1)
            i+=1
    p1_o = p1_o.where(p1_o>=0, 1)
    
    negativo = bool((p1_o < 0).any().to_numpy().any())
    #
    print('Negativo final para percentil 20:',negativo)
    ###########
    positivo = bool((p1 > 100).any().to_numpy().any())
    i = 1
    if positivo:
        print('Hay valores mayores a 100 para percentil 20, corregimos')
        while i<=iter:
            discrepancy = xr.where(p1>100., p1-99, 0)
            #sumamos la mitad a donde corresponda
            p2_o = p2 + 0.5*discrepancy
            p1_o = p1_o.where(p1<=100, 99)
            i+=1
    positivo = bool((p1_o > 100).any().to_numpy().any())
    if positivo:
        p1_o = p1_o.where(p1_o<=100, 99)
    positivo = bool((p1_o > 100).any().to_numpy().any())
    print('Positivo final para percentil 20:', positivo)

    ##################################################
    ##################################################
    #Se trabaja con prob percentil 80
    negativo = bool((p2 < 0).any().to_numpy().any())
    i = 1
    if negativo:
        print('Hay valores bajo 0 para percentil 80, corregimos')
        while i<=iter:
            discrepancy = xr.where(p2<0, p2 - 1, 0)
            #sumamos la mitad a donde corresponda
            p1_o = p1 + 0.5*discrepancy
            p2_o = p2_o.where(p2>=0, 1)
            i+=1
    negativo = bool((p2_o < 0).any().to_numpy().any())
    if negativo:
        p2_o = p2_o.where(p2_o>=0, 0.)
    p2_o = p2_o.where(p2_o>=0, 0.)
    negativo = bool((p2_o < 0).any().to_numpy().any())
    print('Negativo final para percentil 80:',negativo)

    #
    positivo = bool((p2 > 100).any().to_numpy().any())
    i = 1
    if positivo:
        print('Hay valores mayores a 100 para percentil 80, corregimos')
        while i<=iter:
            discrepancy = xr.where(p2>100., p2 - 99, 0)
            #sumamos la mitad a donde corresponda
            p1_o = p1 + 0.5*discrepancy
            p2_o = p2_o.where(p2<=100, 99)
            i+=1
    positivo = bool((p2_o > 100).any().to_numpy().any())
    if positivo:
        p2_o = p2_o.where(p2_o<=100, 99)
    
    positivo = bool((p2_o > 100).any().to_numpy().any())
    print('Positivo final para percentil 80:', positivo)
    p1_o = p1_o.where(p1_o>=0, 1)
    p1_o = p1_o.where(p1_o<=100, 99)
    return p1_o, p2_o




