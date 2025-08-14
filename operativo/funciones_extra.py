
import re
import os
import glob
import requests
import shutil
import validators
import numpy as np
import pandas as pd
import datetime as dt

import cartopy.crs as ccrs
import cartopy.feature as cpf
import matplotlib.pyplot as plt

from cartopy.io import shapereader
from matplotlib import colors as c
from cartopy.mpl.geoaxes import GeoAxes
from typing import cast


def parse_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Use regex to match the variable name and value
            match = re.match(r'(\w+)\s*=\s*"(.*)"', line.strip())
            if match:
                config[match.group(1)] = match.group(2)
    return config


def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         raise ValueError


def gen_url_download(fecha, variable='tas', tipo='forecast', conj='ECCC', modelo='GEPS8'):
    """
    Este es el tipo de links hay que generar:
        https://iridl.ldeo.columbia.edu/SOURCES/.Models/.SubC/.ECCC/.GEPS8/.forecast/.tas/
            X/%2882W%29%2833W%29RANGEEDGES/
            Y/%2857S%29%288S%29RANGEEDGES/
            S/%280000%205%20Aug%202024%29%280000%205%20Aug%202024%29RANGEEDGES/
    """

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


def descarga_pronostico(fecha, variable, tipo, conj, modelo, out_folder):
    url_out = gen_url_download(fecha, variable, tipo, conj, modelo)
    out_file = out_folder + variable + '_' + modelo + '_' + fecha.strftime('%Y%m%d%H%M') + '_forecast.nc'
    if os.path.isfile(out_file):
        print('El archivo ya esta descargado y disponible')
    else:
        print('Descargando archivo y guardando en:', out_file)
        if validators.url(url_out):
            print('Descargando archivo', modelo, 'para la fecha:',fecha)
            with requests.get(url_out, stream=True) as r:
                shutil.copyfileobj(r.raw, out_file)
        else:
            print("Invalid URL")
    
    return out_file


def descarga_pronostico_CFSv2(fecha, variable, out_folder):

    tipo = 'forecast'
    conj = 'NCEP'
    modelo = 'CFSv2'

    for fechai in [fecha-dt.timedelta(days=int(i)) for i in np.arange(0,5)]:
        url_out = gen_url_download(fechai, variable, tipo, conj, modelo)
        out_file = out_folder + variable + '_' + modelo + '_' + fechai.strftime('%Y%m%d%H%M') + '_forecast.nc'
        if os.path.isfile(out_file):
            continue
        else:
            if validators.url(url_out):
                print('Descargando archivo CFSv2 para la fecha:', fechai)
                with requests.get(url_out, stream=True) as r:
                   shutil.copyfileobj(r.raw, out_file)
            else:
                print("Invalid URL")
    out_files = sorted(glob.glob(out_folder + '*' + modelo + '*.nc'), reverse=True)
    
    return out_files


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

    f_model = []
    sem1_i, sem2_i, sem3_i, sem4_i = pd.NaT, pd.NaT, pd.NaT, pd.NaT

    # Se utiliza para ajustar con modelos que no sean
    # GEFS (L=34) ni GEPS8 (L=39) /GEPS7 (L=32)
    # GEOS_V2p1 (L=45)
    if 'L' in list(ds.dims):

        N = ds.sizes['L']  # Largo de pronóstico
        semanas = np.zeros(N)

        # Fechas correspondientes al inicio de las semanas 1, 2 y 3/4 y 5
        if hcast == 0:
            f_model = (ds.S+ds.L).values[0]
            if pd.Timestamp(f_model[0]).date() <= miercoles.date():
                # El modelo tiene datos antes del miercoles guía.
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
                # El modelo tiene datos antes del miercoles guía.
                # Usamos la primera semana desde el jueves para alinear con GEFS esa semana.
                sem1_i = pd.Timestamp(miercoles + dt.timedelta(days=1) + dt.timedelta(hours=12))
            else:
                sem1_i = pd.Timestamp(f_model[0])
            sem2_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=8) + dt.timedelta(hours=12))
            sem3_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=15) + dt.timedelta(hours=12))
            sem4_i = pd.Timestamp(miercoles.replace(year=1960) + dt.timedelta(days=29) + dt.timedelta(hours=12))
        elif hcast == 2:
            f_model = (ds.S+ds.L).values
            if pd.Timestamp(f_model[0]) <= miercoles:
                # El modelo tiene datos antes del miercoles guía.
                # Usamos la primera semana desde el jueves para alinear con GEFS esa semana.
                sem1_i = pd.Timestamp(miercoles + dt.timedelta(days=1) + dt.timedelta(hours=12))
            else:
                sem1_i = pd.Timestamp(f_model[0])
            sem2_i = pd.Timestamp(miercoles + dt.timedelta(days=8) + dt.timedelta(hours=12))
            sem3_i = pd.Timestamp(miercoles + dt.timedelta(days=15) + dt.timedelta(hours=12))
            sem4_i = pd.Timestamp(miercoles + dt.timedelta(days=29) + dt.timedelta(hours=12))
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
            # El modelo tiene datos antes del miercoles guía.
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

    proj_lcc = ccrs.PlateCarree()

    # Comenzamos la Figura
    fig = plt.figure(figsize=figure_size)
    ax = fig.add_subplot(1, 1, 1, projection=proj_lcc)

    # Cast tipo de ax. Para evitar warnings al llamar al los siguientes métodos:
    # ax.coastlines, ax.add_feature, ax.add_geometries. ax. set_extent
    ax = cast(GeoAxes, ax)

    # Agregar límites de paises
    ax.coastlines(resolution='10m')  # type: ignore
    ax.add_feature(cpf.BORDERS, linestyle='-')  # type: ignore

    # Agregar límites administrativos de nivel 1
    shp_name = shapereader.natural_earth(
        resolution='10m', category='cultural', name='admin_1_states_provinces_lines')
    geoms, paises = [], ["Argentina", "Bolivia", "Brazil", "Chile", "Paraguay", "Peru", "Uruguay"]
    for country in shapereader.Reader(shp_name).records():
        if country.attributes['ADM0_NAME'] in paises:
            geoms.append(country.geometry)
    ax.add_geometries(geoms, proj_lcc, edgecolor='grey', facecolor='none', linewidth=0.5)

    # Extensión del mapa
    l_lat, l_lon = llat, np.array(llon) % 360  # Pasamos lon de [-180, 180] a [0, 360]
    ax.set_extent([l_lon[0], l_lon[1], l_lat[0], l_lat[1]], crs=proj_lcc)

    # Posición del eje (desplazamos un poco a la izquierda y más abajo)
    pos1 = ax.get_position()  # get the original position
    pos2 = (pos1.x0 - 0.05, pos1.y0 - 0.06,  pos1.width*1.16, pos1.height*1.22)
    ax.set_position(pos2)  # set a new position

    return fig, ax


def mapa_probabilidad(variable, prob, percentil, week, modelo, f1, f2, c_out, corr=True):

    # Extension del mapa
    llat = [-57, -8]
    llon = [-82, -33]

    # Definir valores por defecto
    titulo = ''
    c_pp = ['#fff']
    
    # Titulo fechas:
    titulof = 'Inicio: ' + f1.strftime('%HH %d/%m/%Y') + '\n ' + f2.strftime('%d/%m/%Y')

    # Paleta colores
    if ((percentil == '20') or (percentil == '50-')) & (variable=='tas'):
        if corr:
            titulo = 'Prob. Corr. por debajo del percentil ' + percentil[0:2]
        else:
            titulo = 'Prob. por debajo del percentil ' + percentil[0:2]
        # colores generados con: grDevices::colorRampPalette(RColorBrewer::brewer.pal(9, 'YlGnBu'))(10)
        c_pp = ['#FFFFD9', '#EFF8B5', '#CFECB3', '#97D6B8', '#5CC0C0', '#30A5C2', '#1E80B8', '#2254A3', '#21318D', '#081D58']
    elif ((percentil == '80') or (percentil == '50+')) & (variable=='tas'):
        if corr:
            titulo = 'Prob. Corr. por encima del percentil ' + percentil[0:2]
        else:
            titulo = 'Prob. por encima del percentil ' + percentil[0:2]
        # colores generados con: grDevices::colorRampPalette(RColorBrewer::brewer.pal(9, 'YlOrRd'))(10)
        c_pp = ['#FFFFCC', '#FFEFA4', '#FEDD7F', '#FEBF5A', '#FD9D43', '#FC7134', '#F33C25', '#DA141E', '#B60026', '#800026']
    elif ((percentil == '20') or (percentil == '50-')) & (variable=='pr'):
        if corr:
            titulo = 'Prob. Corr. por debajo del percentil ' + percentil[0:2]
        else:
            titulo = 'Prob. por debajo del percentil ' + percentil[0:2]
        # colores generados con: grDevices::colorRampPalette(RColorBrewer::brewer.pal(9, 'YlOrBr'))(10)
        c_pp = ['#FFFFE5', '#FFF7C0', '#FEE79A', '#FECE65', '#FEAC39', '#F6861F', '#E1640E', '#C04602', '#933204', '#662506']
    elif ((percentil == '80') or (percentil == '50+')) & (variable=='pr'):
        if corr:
            titulo = 'Prob. Corr. por encima del percentil ' + percentil[0:2]
        else:
            titulo = 'Prob. por encima del percentil ' + percentil[0:2]
        # colores generados con: grDevices::colorRampPalette(RColorBrewer::brewer.pal(9, 'PuBuGn'))(10)
        c_pp = ['#FFF7FB', '#EEE4F1', '#D6D4E8', '#B4C3DE', '#83B1D4', '#519DC8', '#248BAE', '#017C7F', '#016755', '#014636']

    c_map = c.ListedColormap(c_pp)
    c_map.set_bad(color='deeppink')
    bounds = np.array([0, 10.01, 20.01, 30.01, 40.01, 50.01, 60.01, 70.01, 80.01, 90.01, 100.01])
    norm = c.BoundaryNorm(boundaries=bounds, ncolors=len(c_pp))

    # Datos para el mapa
    datap = prob.sel(semanas=week).to_numpy()
    x = prob.X.to_numpy()
    y = prob.Y.to_numpy()
    data = datap.copy()
    data[datap < 0] = np.nan
    data[datap > 100] = np.nan

    fig, ax = mapa_base(llat, llon)

    ax.pcolormesh(x, y, data, cmap=c_map, norm=norm, transform=ccrs.PlateCarree(), alpha=0.8)

    ax.set_title(titulo, loc='left', fontsize=7)

    if week == 3:
        ax.set_title('Semanas 3 y 4; ' + titulof, loc='right', fontsize=7)
        if corr:
            nome_fig = c_out + 'pronostico_corregido_semana_3y4_' + modelo + '.jpg'
        else:
            nome_fig = c_out + 'pronostico_semana_3y4_' + modelo + '.jpg'
        plt.savefig(nome_fig, dpi=150, bbox_inches='tight')
    else:
        ax.set_title('Semana ' + str(week) + '; ' + titulof, loc='right', fontsize=7)
        if corr:
            nome_fig = c_out + 'pronostico_corregido_semana_' + str(week) + '_' + modelo +'.jpg'
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
    c_map = c.ListedColormap(colors)

    # Generar mapa
    fig, ax = mapa_base(llat, llon)
    ax.pcolormesh(x, y, data, cmap=c_map, vmin=0, vmax=1, transform=ccrs.PlateCarree())
    ax.set_title(titulo, loc='left', fontsize=7)
    ax.set_title(titulof, loc='right', fontsize=7)
    plt.savefig(nome_fig, dpi=150, bbox_inches='tight')
