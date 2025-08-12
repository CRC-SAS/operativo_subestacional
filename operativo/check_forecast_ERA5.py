
import xarray as xr
import pandas as pd
import datetime as dt

from funciones_extra import mapa_chequeo


d0 = xr.open_dataset('../datos/operativo/forecast/tas/202501220000/tas_GEFSv12_CPC_202501220000_forecast.nc').tas
print(d0)

fi = [dt.datetime(2025,1,23), dt.datetime(2025,1,30), dt.datetime(2025,2,6)]
ff = [dt.datetime(2025,1,29), dt.datetime(2025,2,5), dt.datetime(2025,2,19)]
ds = xr.open_dataset('../datos/2025_diario.nc')
t2m = ds.t2m
t_week = t2m.sortby('valid_time', ascending=False).rolling(valid_time=7, min_periods=1).mean().sortby('valid_time', ascending=True)
t_2week = t2m.sortby('valid_time', ascending=False).rolling(valid_time=14, min_periods=1).mean().sortby('valid_time', ascending=True)
ds0 = xr.open_dataset('../datos/clim/tmean/tmean_weeklymean_pctile80_smooth.nc').tmean
ds1 = xr.open_dataset('../datos/clim/tmean/tmean_2weeklymean_pctile80_smooth.nc').tmean


c_out = '../figuras/operativo/tas/202501220000/'

for fecha, fecha_f, semana in zip(fi, ff, ['semana1', 'semana2', 'semana3y4']):
    ####
    start_date = pd.to_datetime(d0['S'].values[0])  # Get the starting date
    target_date_pd = pd.to_datetime(fecha) + dt.timedelta(hours=12)
    dates = [start_date + td for td in d0['L'].values]
    # 2. Find the index of the target date
    target_index = dates.index(target_date_pd)
    da_selected = d0.isel({'L': target_index})
    print(da_selected)
    ###
    
    f_old = fecha.replace(year=1960)
    if semana == 'semana3y4':
        dato = t_2week.sel(valid_time=fecha)
        dato = dato.rename({'longitude': 'X','latitude': 'Y'})
        dato = dato.interp_like(da_selected)
        print(dato)
        percentil = ds1.sel(S=f_old)
        new_index = [fecha]
        percentil = percentil.assign_coords(S=fecha)
        percentil = percentil.rename({'longitude': 'X','latitude': 'Y'})
        percentil = percentil.interp_like(da_selected)
    else:
        dato = t_week.sel(valid_time=fecha)
        dato = dato.rename({'longitude': 'X','latitude': 'Y'})
        dato = dato.interp_like(da_selected)
        print(dato)
        percentil = ds0.sel(S=f_old)
        new_index = [fecha]
        percentil = percentil.assign_coords(S=fecha)
        percentil = percentil.rename({'longitude': 'X','latitude': 'Y'})
        percentil = percentil.interp_like(da_selected)
    #
    print(percentil)
    
    #
    comparison = dato > percentil
    
    nome_fig = c_out + 'chequeo_pronostico_corregido_semana_' + semana + '.jpg'
    mapa_chequeo(comparison, fecha, fecha_f, nome_fig)
    
    
    

    




