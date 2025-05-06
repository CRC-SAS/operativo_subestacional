import os
import requests
import shutil
import validators
import numpy as np
import pandas as pd
import datetime as dt

import cartopy.crs as ccrs
import cartopy.feature as cpf
from cartopy.io.shapereader import Reader
from cartopy.io.shapereader import natural_earth

import matplotlib.pyplot as plt
from matplotlib import colors as c



def gen_url_download(fecha, variable='tas', tipo='forecast', conj='ECCC', modelo='GEPS8'):
    '''
    Este tipo de links hay que generar
    #https://iridl.ldeo.columbia.edu/SOURCES/.Models/.SubC/
    # .ECCC/.GEPS8/.forecast/.tas/
    # X/%2882W%29%2833W%29RANGEEDGES/
    # Y/%2857S%29%288S%29RANGEEDGES/
    # S/%280000%205%20Aug%202024%29%280000%205%20Aug%202024%29RANGEEDGES/
    '''
    #dia = fecha.strftime('%-d')
    dia = fecha.strftime('%#d')
    mes = fecha.strftime('%b')
    year = fecha.strftime('%Y')
    url_base = 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.SubC/'
    url_out = url_base + '.' + conj + '/.' + modelo + '/.' + tipo + '/.' + variable + '/' +\
              'X/%2882W%29%2833W%29RANGEEDGES/Y/%2857S%29%288S%29RANGEEDGES/' +\
              'S/%280000%20' + dia + '%20' + mes +'%20' + year + \
              '%29%280000%20' + dia + '%20' + mes +'%20' + year + '%29RANGEEDGES/' +\
              'data.nc'
    return url_out

def descarga_pronostico(fecha, variable, tipo, conj, modelo, outfolder):
    url_out = gen_url_download(fecha, variable, tipo, conj, modelo)
    out_file = outfolder + variable + '_' + modelo + '_' + fecha.strftime('%Y%m%d%H%M') + '_forecast.nc'
    if os.path.isfile(out_file):
        print('El archivo ya esta descargado y disponible')
    else:
        print('Descargando archivo y guardando en:', out_file)
        valid=validators.url(url_out)
        if valid==True:
            print(fecha)
            with requests.get(url_out, stream=True) as r:
                with open(out_file, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        else:
            print("Invalid url")
    
    return out_file

def grouping_coord(ds):
    if 'L' in list(ds.dims):
        N = ds.sizes['L']  # Largo de pronóstico
        semanas = np.ones(N)
        semanas[7:14] = 2
        semanas[14:28] = 3
        semanas[28:] = 5
        ds = ds.assign_coords(semanas=('L', semanas))
    else:
        N = ds.sizes['S']  # Largo de pronóstico
        semanas = np.ones(N)
        semanas[7:14] = 2
        semanas[14:28] = 3
        semanas[28:] = 5
        ds = ds.assign_coords(semanas=('S', semanas))
    return ds


def grouping_coord_fecha(ds, miercoles, hcast=0):
    # Se utiliza para ajustar con modelos que no sean
    # GEFS (L=34) ni GEPS8 (L=39) /GEPS7 (L=32)
    # GEOS_V2p1 (L=45)
    #
    print('hcast=', hcast)     
    if 'L' in list(ds.dims):
        
        N = ds.sizes['L']  # Largo de pronóstico
        semanas = np.zeros(N)
        # Fechas correspondiente a inicio semana 1, 2 y 3/4 y 5
        if hcast == 0:
            f_model = (ds.S+ds.L).values[0]
            if pd.Timestamp(f_model[0]).date() <= miercoles.date():
                
                # El modelo tiene datos antes del miercoles guia.
                # Usamos la primera semana desde el jueves para alinear con GEFS esa semana.
                sem1_i = pd.Timestamp(miercoles + dt.timedelta(days=1) + dt.timedelta(hours=12))
            else:
                sem1_i = pd.Timestamp(f_model[0])
            sem2_i = pd.Timestamp(miercoles + dt.timedelta(days=8) + dt.timedelta(hours=12))
            sem3_i = pd.Timestamp(miercoles + dt.timedelta(days=15) + dt.timedelta(hours=12))
            sem4_i = pd.Timestamp(miercoles + dt.timedelta(days=29) + dt.timedelta(hours=12))
        elif hcast == 1:
            f_model = (ds.S+ds.L).values
            if pd.Timestamp(f_model[0]) <= miercoles:
                # El modelo tiene datos antes del miercoles guia.
                # Usamos la primera semana desde el jueves para alinear con GEFS esa semana.
                sem1_i = pd.Timestamp(miercoles + dt.timedelta(days=1) + dt.timedelta(hours=12))
            else:
                sem1_i = pd.Timestamp(f_model[0])
            #sem1_i = pd.Timestamp(f_model[0])
            sem2_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=8) + dt.timedelta(hours=12))
            sem3_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=15) + dt.timedelta(hours=12))
            sem4_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=29) + dt.timedelta(hours=12))
        #
        fechas_m = np.array([pd.Timestamp(a)==sem1_i for a in f_model])
        i1 = fechas_m.argmax()
        #
        fechas_m = np.array([pd.Timestamp(a)==sem2_i for a in f_model])
        i2 = fechas_m.argmax()
        #
        fechas_m = np.array([pd.Timestamp(a)==sem3_i for a in f_model])
        i3 = fechas_m.argmax()
        #
        semanas[i1:i2] = 1
        semanas[i2:i2+7] = 2
        semanas[i3:i3+14] = 3
        semanas[i3+14:] = 5
        ds = ds.assign_coords(semanas=('L', semanas))
    else:
        N = ds.sizes['S']  # Largo de pronóstico
        semanas = np.ones(N)
        f_model = (ds.S).values
        if pd.Timestamp(f_model[0]) <= miercoles:
            # El modelo tiene datos antes del miercoles guia.
            # Usamos la primera semana desde el jueves para alinear con GEFS esa semana.
            sem1_i = pd.Timestamp(miercoles + dt.timedelta(days=1) + dt.timedelta(hours=12))
        else:
            sem1_i = pd.Timestamp(f_model[0])
        sem2_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=8))
        sem3_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=15))
        sem4_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=29))

        # Indice correspondiente a inicio semana 2 y 3
        fechas_m = np.array([pd.Timestamp(a)==sem2_i for a in f_model])
        i2 = fechas_m.argmax()
        #
        fechas_m = np.array([pd.Timestamp(a)==sem3_i for a in f_model])
        i3 = fechas_m.argmax()
        #
        semanas[i2:i2+7] = 2
        semanas[i3:i3+14] = 3
        semanas[i3+14:] = 5
        #
        ds = ds.assign_coords(semanas=('S', semanas))
    fechas_iniciales = [sem1_i, sem2_i, sem3_i, sem4_i]
    f_out = [a.date() for a in fechas_iniciales]
    return ds, f_out



def mapa_base(llat, llon, figure_size=(6,8)):
    """
    Mapa base para graficar las variables
    """

    l_lat = llat
    l_lon = np.array(llon) % 360  #Pasamos lon en [-180, 180] a [0, 360]
    
    # Comenzamos la Figura
    fig = plt.figure(figsize=figure_size)
    proj_lcc = ccrs.PlateCarree()
    ax = plt.axes(projection=proj_lcc)
    shp = Reader(natural_earth(resolution='10m', category='cultural',
                               name='admin_1_states_provinces_lines'))
    
    countries = shp.records()
    ax.coastlines(resolution='10m')
    ax.add_feature(cpf.BORDERS, linestyle='-')
    for country in countries:
        ax.add_geometries( [country.geometry], ccrs.PlateCarree(),
                            edgecolor='grey', facecolor='none', linewidth=0.5 )
    # Extension del mapa
    ax.set_extent([l_lon[0], l_lon[1], l_lat[0], l_lat[1]], crs=proj_lcc)
    # Posicion del eje (desplazamos un poco a la izquierda y más abajo)
    pos1 = ax.get_position() # get the original position
    pos2 = [pos1.x0 - 0.05, pos1.y0 - 0.06,  pos1.width*1.16, pos1.height*1.22]
    ax.set_position(pos2) # set a new position

    return fig, ax

def mapa_probabilidad(variable, prob, percentil, week, modelo, f1, f2, c_out, corr=True):
    # Extension del mapa
    llat = [-57, -8]
    llon = [-82, -33]
    
    # Titulo fechas:
    titulof = 'Inicio: ' + f1.strftime('%HH %d/%m/%Y') + '\n ' + f2.strftime('%d/%m/%Y')

    # Paleta colores
    if ((percentil == '20') or (percentil == '50-')) & (variable=='tas'):
        if corr:
            titulo = 'Prob. Corr. por debajo del percentil ' + percentil[0:2]
        else:
            titulo = 'Prob. por debajo del percentil ' + percentil[0:2]
        #c_pp = ['dimgray', '#ffffff', '#bdc9e1', '#74a9cf', '#2b8cbe', '#045a8d', 'deeppink']
        #c_pp = ['#ffffff', '#bdc9e1', '#74a9cf', '#2b8cbe', '#045a8d']
        c_pp = ['#ffffff','#edf8b1','#c7e9b4','#7fcdbb','#41b6c4','#1d91c0','#225ea8','#253494','#081d58']
    elif ((percentil == '80') or (percentil == '50+')) & (variable=='tas'):
        if corr:
            titulo = 'Prob. Corr. por encima del percentil ' + percentil[0:2]
        else:
            titulo = 'Prob. por encima del percentil ' + percentil[0:2]
        #c_pp = ['#ffffff', '#fdae6b', '#fd8d3c', '#e6550d', '#a63603']
        c_pp = ['#ffffff', '#ffeda0','#fed976','#feb24c','#fd8d3c','#fc4e2a','#e31a1c','#bd0026','#800026']
    elif ((percentil == '20') or (percentil == '50-')) & (variable=='pr'):
        if corr:
            titulo = 'Prob. Corr. por debajo del percentil ' + percentil[0:2]
        else:
            titulo = 'Prob. por debajo del percentil ' + percentil[0:2]
        c_pp = ['#ffffff', '#fdae6b', '#fd8d3c', '#e6550d', '#a63603']
    elif ((percentil == '80') or (percentil == '50+')) & (variable=='pr'):
        if corr:
            titulo = 'Prob. Corr. por encima del percentil ' + percentil[0:2]
        else:
            titulo = 'Prob. por encima del percentil ' + percentil[0:2]
        c_pp = ['#ffffff', '#d0d1e6', '#67a9cf', '#02818a', '#014636']


    cMap = c.ListedColormap(c_pp)
    cMap.set_bad(color='deeppink')
    #cMap.set_extremes(under='dimgrey', over='deeppink')
    #bounds = np.array([0,20.01,40,60,80,100])
    bounds = np.array([0,20.01,30.01,40.01,50.01,60.01,70.01,80.01,90.01,100.01])
    norm = c.BoundaryNorm(boundaries=bounds, ncolors=len(c_pp))#, extend='both')
    # Datos para el mapa
    datap = prob.sel(semanas=week).to_numpy()
    print(np.min(datap), np.mean(datap), np.max(datap))
    x = prob.X.to_numpy()
    y = prob.Y.to_numpy()
    data = datap.copy()
    data[datap<0] = np.nan
    data[datap>100] = np.nan

    fig, ax = mapa_base(llat, llon)
    #CS = ax.contourf(x, y, data, levels=bounds, cmap=cMap, norm=norm, transform=ccrs.PlateCarree())
    CS = ax.pcolormesh(x,y,data, cmap=cMap, norm=norm, transform=ccrs.PlateCarree(), alpha=0.8)
    #cb = fig.colorbar(CS, orientation='vertical', shrink=0.6, pad = 0.01)
    ax.set_title(titulo, loc='left', fontsize=7)
    if week == 3:
        ax.set_title('Semanas 3 y 4; ' + titulof, loc='right', fontsize=7)
        if corr:
            nome_fig = c_out + 'pronostico_corregido_semana_3y4_' + modelo + '.jpg'
            plt.savefig(nome_fig, dpi=150, bbox_inches='tight')
        else:
            nome_fig = c_out + 'pronostico_semana_3y4_' + modelo + '.jpg'
            plt.savefig(nome_fig, dpi=150, bbox_inches='tight')
    else:
        ax.set_title('Semana ' + str(week) + '; ' + titulof, loc='right', fontsize=7)
        if corr:
            nome_fig = c_out + 'pronostico_corregido_semana_' + str(week) + '_' + modelo +'.jpg'
            plt.savefig(nome_fig, dpi=150, bbox_inches='tight')
        else:
            nome_fig = c_out + 'pronostico_semana_' + str(week) + '_' + modelo + '.jpg'
            plt.savefig(nome_fig, dpi=150, bbox_inches='tight')
    
    
    plt.close(fig)

def mapa_chequeo(chequeo, f1, f2, nome_fig):
    # Extension del mapa
    llat = [-57, -8]
    llon = [-82, -33]
    x = chequeo.X.to_numpy()
    y = chequeo.Y.to_numpy()
    data = chequeo.copy()
    # Titulo fechas:
    titulof = 'Inicio: ' + f1.strftime('%HH %d/%m/%Y') + '\n ' + f2.strftime('%d/%m/%Y')
    titulo = 'Chequeo pronostico percentil 80 '
    # Define the custom colormap
    colors = ['white', 'limegreen']
    cMap = c.ListedColormap(colors)
    fig, ax = mapa_base(llat, llon)
    CS = ax.pcolormesh(x,y,data, cmap=cMap, vmin=0, vmax=1, transform=ccrs.PlateCarree())
    ax.set_title(titulo, loc='left', fontsize=7)
    ax.set_title(titulof, loc='right', fontsize=7)
    plt.savefig(nome_fig, dpi=150, bbox_inches='tight')

