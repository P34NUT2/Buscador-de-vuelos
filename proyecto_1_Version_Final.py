import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
from collections import deque
import heapq
import streamlit as st
import pprint 

################################################################################

#funciones 
def procesar_texto():
    input_user = st.text_input()
    return input_user    
def tiempos_de_vuelo(f_salida, f_llegada, h_salida, h_llegada):
    salida = datetime.strptime(f'{f_salida} {h_salida}', '%Y-%m-%d %H:%M')
    llegada = datetime.strptime(f'{f_llegada} {h_llegada}', '%Y-%m-%d %H:%M')
    tiempo = ((llegada-salida).total_seconds()/3600)
    return tiempo
def tiempo_logico(f_salida, f_llegada, h_salida, h_llegada):
    salida = datetime.strptime(f'{f_salida} {h_salida}', '%Y-%m-%d %H:%M')
    llegada = datetime.strptime(f'{f_llegada} {h_llegada}', '%Y-%m-%d %H:%M')

    if llegada >= salida:
        return True
    else:
        return False
def dias_y_horas(hora):
    tiempo = timedelta(hours=hora)
    dias = tiempo.days
    hora = tiempo.seconds /3600
    return dias, hora 
def nice_write_origen(input):
    contador = 0
    copia_d_columna = df[['Origen', 'Destino']].copy()
    tam = copia_d_columna.shape[0]

    for _, row in copia_d_columna.iterrows():
        contador += 1

        if row['Origen'] == input:
            return True

    if contador == tam:
        return False 
def nice_write_destino(input):
    contador = 0
    copia_d_columna = df[['Origen', 'Destino']].copy()
    tam = copia_d_columna.shape[0]

    for _, row in copia_d_columna.iterrows():
        contador += 1

        if row['Destino'] == input:
            return True

    if contador == tam:
        return False
    
def verificador_ortografia():
    lugar_d_partida = st.text_input("Ingresa tu lugar de partida:")
    if lugar_d_partida and nice_write_origen(lugar_d_partida) == True:  
        lugar_d_destino = st.text_input("Ingresa tu destino:")
        if lugar_d_destino and nice_write_destino(lugar_d_destino) == True:  
            if lugar_d_partida == lugar_d_destino:
                st.write("El lugar de partida y el destino son iguales.")
                return False, lugar_d_partida, lugar_d_destino
            return True, lugar_d_partida, lugar_d_destino
        elif lugar_d_destino == '9':
            return False, '', 'a'
    elif lugar_d_partida == '9':
        return False, '', 'a'

    return None, '', ''
def dibujar_grafos(grafo,titulo):
    pos = nx.spring_layout(grafo)
    nx.draw(grafo, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, font_weight='bold')
    edge_labels = nx.get_edge_attributes(grafo, 'weigth')
    nx.draw_networkx_edge_labels(grafo, pos, edge_labels=edge_labels)

    plt.title(titulo)
    plt.show()
def tiempo_y_horas(ruta):
    horas = 0
    dinero = 0

    for i in range(len(ruta)-1):
        ori = ruta[i]
        dest = ruta[i + 1]
        vuelo_actual = df[(df['Origen'] == ori) & (df['Destino'] == dest)]

        if not vuelo_actual.empty:
            dinero += vuelo_actual['Precio_Vuelo'].values[0]
            horas += tiempos_de_vuelo(vuelo_actual['Fecha_Salida'].values[0], 
                                    vuelo_actual['Fecha_Llegada'].values[0], 
                                    vuelo_actual['Hora_Salida_Origen'].values[0], 
                                    vuelo_actual['Hora_Llegada_Destino'].values[0])
    return dinero, horas
def busqueda_amplitud(grafo, inicio, objetivo):
    visitados = set()
    rutas=[]
    cola = deque([(inicio, [inicio])])

    while cola:
        nodo_actual, camino = cola.popleft()
        if nodo_actual == objetivo:
            rutas.append(camino)
        elif nodo_actual not in visitados:
            visitados.add(nodo_actual)
            for vecino in grafo[nodo_actual]:
                if vecino not in visitados:
                    nueva_ruta = camino + [vecino]
                    cola.append((vecino, nueva_ruta))
    if not rutas:
        return None
    else:
        return rutas
    
def busqueda_profundidad(grafo, inicio, objetivo, visitados=None, camino=None, caminos_encontrados=None):
    
    if visitados is None:
        visitados = set()
    if camino is None:
        camino = []
    if caminos_encontrados is None:
        caminos_encontrados = []

    camino.append(inicio)
    visitados.add(inicio)

    if inicio == objetivo:
        caminos_encontrados.append(camino.copy())
    else:
        for vecino in grafo[inicio]:
            if vecino not in visitados:
                busqueda_profundidad(grafo, vecino, objetivo, visitados, camino, caminos_encontrados)

    camino.pop()
    visitados.remove(inicio)

    return caminos_encontrados
def costo_uniforme(inicio, objetivo, grafo, costo_o_tiempo):
    cola_prioridad = []
    heapq.heappush(cola_prioridad, (0, inicio, [inicio]))  
    visitados = set()
    
    while cola_prioridad:
        costo_actual, nodo_actual, camino = heapq.heappop(cola_prioridad)
        if nodo_actual == objetivo:
            return costo_actual, camino
        
        if nodo_actual not in visitados:
            visitados.add(nodo_actual)
            for vecino, costo in grafo[nodo_actual].items():
                if vecino not in visitados: # Visitamos solo los vecinos NO visitados
                    nuevo_costo = costo_actual + costo[costo_o_tiempo]
                    nuevo_camino = camino + [vecino]
                    heapq.heappush(cola_prioridad, (nuevo_costo, vecino, nuevo_camino))

    return float('inf'), []


################################################################################


#lectura del data frame
#aca leemos el data frame
data_frame = pd.read_csv('Vuelos_100_Registros_sin_segundos_v2.csv')
#decido hacer una copia para trabajr en este y no mover ningun dato original
# y asi poder experimentar con el sin perder o mopdificar tipos de datos
df = data_frame.copy()


#creacion de los grafos
grafo_tiempo = nx.DiGraph()
grafo_costo = nx.DiGraph()
#aca puse _, por que asi ignora el indice y se puede iterar mejor por que 
for _, row in df.iterrows():
    #aca asigno un valor para despues con la ayuda de la libreria networkx asignarlas al grafo
    origen = row['Origen']
    destino = row['Destino']
    
    if tiempo_logico(row['Fecha_Salida'], row['Fecha_Llegada'], row['Hora_Salida_Origen'], row['Hora_Llegada_Destino']) == True:
        tiempos = tiempos_de_vuelo(row['Fecha_Salida'], row['Fecha_Llegada'], row['Hora_Salida_Origen'], row['Hora_Llegada_Destino'])
        #aca se pone nodo 1como origen y destino como nodo2 osea el final y en medio pongo tiempos de vuelo osea el borde o el palito
        grafo_tiempo.add_edge(origen, destino, tiempo = tiempos)

#ahora aca con la misma tecnica creamos el de costo
for _, row in df.iterrows():
    #aca asigno un valor para despues con la ayuda de la libreria networkx asignarlas al grafo
    origen = row['Origen']
    destino = row['Destino']
    precio = row['Precio_Vuelo']
    if tiempo_logico(row['Fecha_Salida'], row['Fecha_Llegada'], row['Hora_Salida_Origen'], row['Hora_Llegada_Destino']) == True:
        #aca se pone nodo 1como origen y destino como nodo2 osea el final y en medio pongo costos osea el borde o el palito
        grafo_costo.add_edge(origen, destino, costos = precio)

grafo_dic_tiempo = {}

for nodo, contenido in grafo_tiempo.adjacency():
    grafo_dic_tiempo[nodo] = dict(contenido)

grafo_dic_costo = {}

for nodo, contenido in grafo_costo.adjacency():
    grafo_dic_costo[nodo] = dict(contenido)


################################################################################
#creacion de la interfaz y del menu 
st.set_page_config(
    page_title="Aero UP",  # Título de la página en el navegador
    page_icon=":sparkles:",                # Ícono que aparece en la pestaña del navegador
    layout="centered",                     # 'wide' para usar todo el ancho de la pantalla
    initial_sidebar_state="collapsed",     # Estado inicial de la barra lateral ('expanded' o 'collapsed')
)

st.title('AeroUP')
st.write('Buscador de vuelos ;)') 
# Crear menú en streamlit
menu = st.sidebar.selectbox(
    "Selecciona una página",
    ["Inicio", "Todas las rutas hacia el destino elegido", "Encontrar ruta por el MENOR COSTO",
    "Encontrar ruta por el MENOR TIEMPO", "Encontrar todas las rutas por PROFUNDIDAD", "Encontrar todas las rutas por AMPLITUD",
    "Grafo de COSTO", "Grafo de TIEMPO"]
)

if menu == "Inicio":
    st.title("Bienvenido o Bienvenida")
    st.write("Esta pagina esta hecha para buscar vuelos, esto nos va encontrar vuelos rapidos con tiempo,\nvuelos baratos o todo tipo de rutas incluso directas")
elif menu == "Todas las rutas hacia el destino elegido":
    st.title("Todas las rutas hacia el destino disponible son:")
    condicion, lugar_d_partida, lugar_d_destino = verificador_ortografia()

    if condicion is None:
        st.write("Esperando entrada del usuario...")

    if condicion == False and lugar_d_destino == lugar_d_partida:
        st.write(f'Ya estás en el destino {lugar_d_destino}, así que el tiempo y dinero son 0\n')
    elif condicion == True:
        st.write('-------------------------')
        st.write('Búsqueda de la ruta que tiene MENOR COSTO')

        cos_minimo, c_minimo = costo_uniforme(lugar_d_partida, lugar_d_destino, grafo_dic_costo, 'costos')
        c_c = []
        c_c.append(c_minimo)

        for lista in c_c:
            costo, tiempo = tiempo_y_horas(lista)
            dia, hora = dias_y_horas(tiempo)
            st.write(f'{"->".join(lista)}, dinero necesario ${costo} y dura {round(tiempo, 2)} horas, o {dia} días y {round(hora, 2)} horas')

        if cos_minimo != float('inf'):
            st.write(f"La ruta con menor costo desde {lugar_d_partida} hasta {lugar_d_destino} es: ${cos_minimo}")
            st.write(f"El camino mínimo es: {' -> '.join(c_minimo)}")
        else:
            st.write(f"No se encontró un camino desde {lugar_d_partida} hasta {lugar_d_destino}")

        st.write('-------------------------')
        st.write('Búsqueda de la ruta que tiene menor tiempo')

        costo_minimo, camino_minimo = costo_uniforme(lugar_d_partida, lugar_d_destino, grafo_dic_tiempo, 'tiempo')
        c_cam = []
        c_cam.append(camino_minimo)

        for lista in c_cam:
            costo, tiempo = tiempo_y_horas(lista)
            dia, hora = dias_y_horas(tiempo)
            st.write(f'{"->".join(lista)}, dinero necesario ${costo} y dura {round(tiempo, 2)} horas, o {dia} días y {round(hora, 2)} horas')

        if costo_minimo != float('inf'):
            st.write(f"La ruta con menor tiempo desde {lugar_d_partida} hasta {lugar_d_destino} es: {round(costo_minimo, 2)} horas")
            st.write(f"El camino mínimo es: {' -> '.join(camino_minimo)}")
        else:
            st.write(f"No se encontró un camino desde {lugar_d_partida} hasta {lugar_d_destino}")

        st.write('-------------------------')
        st.write('Todas las rutas\n')
        st.write('Por amplitud')
        rutas_amplitud = busqueda_amplitud(grafo_dic_tiempo, lugar_d_partida, lugar_d_destino)
        if rutas_amplitud:
            for lista in rutas_amplitud:
                costo, tiempo = tiempo_y_horas(lista)
                dia, hora = dias_y_horas(tiempo)
                st.write(f'{"->".join(lista)}, dinero necesario ${costo} y dura {round(tiempo, 2)} horas, o {dia} días y {round(hora, 2)} horas')
        st.write('-------------------------')
        st.write('Por profundidad')
        rutas_profundidad = busqueda_profundidad(grafo_dic_tiempo, lugar_d_partida, lugar_d_destino)
        if rutas_profundidad:
            for lista in rutas_profundidad:
                costo, tiempo = tiempo_y_horas(lista)
                dia, hora = dias_y_horas(tiempo)
                st.write(f'{"->".join(lista)}, dinero necesario ${costo} y dura {round(tiempo, 2)} horas, o {dia} días y {round(hora, 2)} horas')
elif menu == "Encontrar ruta por menor costo":
    st.title("El vuelo por menor costo es el siguiente:")
    condicion, lugar_d_partida, lugar_d_destino = verificador_ortografia()

    if condicion is None:
        st.write("Esperando entrada del usuario...")

    if condicion == False and lugar_d_destino == lugar_d_partida:
        st.write(f'Ya estás en el destino {lugar_d_destino}, así que el tiempo y dinero son 0\n')
    elif condicion == True:
        cos_minimo, c_minimo = costo_uniforme(lugar_d_partida, lugar_d_destino, grafo_dic_costo, 'costos')
        c_c = []
        c_c.append(c_minimo)

        for lista in c_c:
            costo, tiempo = tiempo_y_horas(lista)
            dia, hora = dias_y_horas(tiempo)
            st.write(f'{"->".join(lista)}, dinero necesario ${costo} y dura {round(tiempo, 2)} horas, o {dia} días y {round(hora, 2)} horas')

        if cos_minimo != float('inf'):
            st.write(f"La ruta con menor costo desde {lugar_d_partida} hasta {lugar_d_destino} es: ${cos_minimo}")
            st.write(f"El camino mínimo es: {' -> '.join(c_minimo)}")
        else:
            st.write(f"No se encontró un camino desde {lugar_d_partida} hasta {lugar_d_destino}")
elif menu == "Encontrar ruta por menor tiempo":
    st.title(f"La ruta por menor tiempo es: ")
    condicion, lugar_d_partida, lugar_d_destino = verificador_ortografia()

    if condicion is None:
        st.write("Esperando entrada del usuario...")

    if condicion == False and lugar_d_destino == lugar_d_partida:
        st.write(f'Ya estás en el destino {lugar_d_destino}, así que el tiempo y dinero son 0\n')
    elif condicion == True:
        costo_minimo, camino_minimo = costo_uniforme(lugar_d_partida, lugar_d_destino, grafo_dic_tiempo, 'tiempo')
        c_cam = []
        c_cam.append(camino_minimo)

        for lista in c_cam:
            costo, tiempo = tiempo_y_horas(lista)
            dia, hora = dias_y_horas(tiempo)
            st.write(f'{"->".join(lista)}, dinero necesario ${costo} y dura {round(tiempo, 2)} horas, o {dia} días y {round(hora, 2)} horas')

        if costo_minimo != float('inf'):
            st.write(f"La ruta con menor tiempo desde {lugar_d_partida} hasta {lugar_d_destino} es: {round(costo_minimo, 2)} horas")
            st.write(f"El camino mínimo es: {' -> '.join(camino_minimo)}")
        else:
            st.write(f"No se encontró un camino desde {lugar_d_partida} hasta {lugar_d_destino}")
elif menu == "Encontrar todas las rutas por profundiad":
    st.title("Las rutas dadas por busqueda por profundidad son:")
    condicion, lugar_d_partida, lugar_d_destino = verificador_ortografia()

    if condicion is None:
        st.write("Esperando entrada del usuario...")

    if condicion == False and lugar_d_destino == lugar_d_partida:
        st.write(f'Ya estás en el destino {lugar_d_destino}, así que el tiempo y dinero son 0\n')
    elif condicion == True:
        rutas_profundidad = busqueda_profundidad(grafo_dic_tiempo, lugar_d_partida, lugar_d_destino)
        if rutas_profundidad:
            for lista in rutas_profundidad:
                costo, tiempo = tiempo_y_horas(lista)
                dia, hora = dias_y_horas(tiempo)
                st.write(f'{"->".join(lista)}, dinero necesario ${costo} y dura {round(tiempo, 2)} horas, o {dia} días y {round(hora, 2)} horas')
elif menu == "Encontrar todas las rutas por amplitud":
    st.title("Las rutas dadas por busqueda por amplitud son:")
    condicion, lugar_d_partida, lugar_d_destino = verificador_ortografia()

    if condicion is None:
        st.write("Esperando entrada del usuario...")

    if condicion == False and lugar_d_destino == lugar_d_partida:
        st.write(f'Ya estás en el destino {lugar_d_destino}, así que el tiempo y dinero son 0\n')
    elif condicion == True:
        rutas_amplitud = busqueda_amplitud(grafo_dic_tiempo, lugar_d_partida, lugar_d_destino)
        if rutas_amplitud:
            for lista in rutas_amplitud:
                costo, tiempo = tiempo_y_horas(lista)
                dia, hora = dias_y_horas(tiempo)
                st.write(f'{"->".join(lista)}, dinero necesario ${costo} y dura {round(tiempo, 2)} horas, o {dia} días y {round(hora, 2)} horas')
elif menu == "Grafo de costo":
    st.title("Grafo costos")
    st.write(grafo_dic_costo)
elif menu == "Grafo de tiempo":
    st.title("Grafo tiempo")
    st.write(grafo_dic_tiempo)