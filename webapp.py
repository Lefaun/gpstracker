import streamlit as st
import requests
import json
from websocket import create_connection
from geopy.distance import geodesic
import pydeck as pdk
import threading
import time

# Configurações da API Traccar
TRACCAR_URL = "https://demo.traccar.org/api"
USERNAME = "vegaspace@gmail.com"  # Substitua pelo seu e-mail da conta Traccar
PASSWORD = "ABCD1234#"              # Substitua pela sua senha da conta Traccar

# Definir uma rota (Sintra, Queluz, Amadora)
ROTA_PREDEFINIDA = [
    (38.8029, -9.3817),  # Sintra
    (38.7566, -9.2546),  # Queluz
    (38.7536, -9.2305),  # Amadora
]

# Função para verificar se o dispositivo está na rota
def verificar_rota(localizacao_atual):
    for ponto in ROTA_PREDEFINIDA:
        distancia = geodesic(localizacao_atual, ponto).meters
        if distancia <= 500:  # Considera "na rota" se estiver a 500 metros de um ponto da rota
            return True
    return False

# Função de autenticação na API do Traccar
def autenticar_traccar():
    response = requests.get(f"{TRACCAR_URL}/session", auth=(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.cookies
    else:
        st.error(f"Erro na autenticação: {response.status_code}")
        return None

# Obter dispositivos da API
def obter_dispositivos(cookies):
    response = requests.get(f"{TRACCAR_URL}/devices", cookies=cookies)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erro ao obter dispositivos: {response.status_code}")
        return []

# Monitoramento em tempo real via WebSocket
def monitorar_em_tempo_real(cookies, localizacoes):
    ws_url = "wss://demo.traccar.org/api/socket"
    ws = create_connection(ws_url, header=[f"Cookie: {cookies.get('JSESSIONID')}"])
    st.session_state['websocket'] = ws  # Guardar WebSocket na sessão

    try:
        while True:
            resultado = ws.recv()
            dados = json.loads(resultado)

            if 'positions' in dados:
                for posicao in dados['positions']:
                    lat = posicao['latitude']
                    lon = posicao['longitude']
                    device_id = posicao['deviceId']
                    na_rota = verificar_rota((lat, lon))
                    status_rota = "na rota" if na_rota else "fora da rota"

                    localizacoes[device_id] = {'latitude': lat, 'longitude': lon, 'status': status_rota}

            time.sleep(2)  # Pequeno intervalo para não sobrecarregar
    except:
        st.error("Conexão encerrada com o WebSocket.")
    finally:
        ws.close()

# Função principal do Streamlit
def main():
    st.title("🚴 Monitoramento de Frotas em Tempo Real")
    st.subheader("Sintra, Queluz e Amadora")

    # Autenticação na API
    cookies = autenticar_traccar()
    if not cookies:
        return

    # Obter lista de dispositivos
    dispositivos = obter_dispositivos(cookies)
    localizacoes = {dispositivo['id']: {'latitude': None, 'longitude': None, 'status': 'Desconhecido'} for dispositivo in dispositivos}

    # Iniciar WebSocket em thread separada
    if 'websocket_thread' not in st.session_state:
        thread = threading.Thread(target=monitorar_em_tempo_real, args=(cookies, localizacoes))
        thread.daemon = True
        thread.start()
        st.session_state['websocket_thread'] = thread

    # Atualização da interface
    while True:
        st.write("### Dispositivos:")
        for dispositivo in dispositivos:
            device_id = dispositivo['id']
            nome = dispositivo['name']
            lat = localizacoes[device_id]['latitude']
            lon = localizacoes[device_id]['longitude']
            status = localizacoes[device_id]['status']

            if lat and lon:
                st.write(f"**{nome}** está em ({lat:.5f}, {lon:.5f}) - **{status}**")
            else:
                st.write(f"**{nome}** - Sem dados de localização")

        # Mapa com localização dos dispositivos
        coords = [{'lat': loc['latitude'], 'lon': loc['longitude']} for loc in localizacoes.values() if loc['latitude']]
        if coords:
            st.map(coords)

        # Atualiza a cada 5 segundos
        time.sleep(5)
        st.experimental_rerun()

if __name__ == "__main__":
    main()
