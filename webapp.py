import requests
import json
from websocket import create_connection
from geopy.distance import geodesic

# Configurações da API Traccar
TRACCAR_URL = "https://demo.traccar.org/api"
USERNAME = "vegaspace@gmail.com"  # Substitua pelo seu e-mail da conta Traccar
PASSWORD = "ABCD1234#"              # Substitua pela sua senha da conta Traccar

# Autenticação e obtenção do token de sessão
def autenticar_traccar():
    response = requests.get(f"{TRACCAR_URL}/session", auth=(USERNAME, PASSWORD))
    if response.status_code == 200:
        print("Autenticado com sucesso!")
        return response.cookies  # Retorna cookies de autenticação para as próximas requisições
    else:
        raise Exception("Erro na autenticação: ", response.status_code)

# Obter dispositivos (bicicletas, veículos, etc.)
def obter_dispositivos(cookies):
    response = requests.get(f"{TRACCAR_URL}/devices", cookies=cookies)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Erro ao obter dispositivos: ", response.status_code)

# Definir uma rota (exemplo simples com coordenadas de Sintra a Amadora)
ROTA_PREDEFINIDA = [
    (38.8029, -9.3817),  # Sintra
    (38.7566, -9.2546),  # Queluz
    (38.7536, -9.2305),  # Amadora
]

# Verificar se o dispositivo está próximo da rota
def verificar_rota(localizacao_atual):
    for ponto in ROTA_PREDEFINIDA:
        distancia = geodesic(localizacao_atual, ponto).meters
        if distancia <= 500:  # Considera "na rota" se estiver a 500 metros de um ponto da rota
            return True
    return False

# Conectar ao WebSocket para atualizações em tempo real
def monitorar_em_tempo_real(cookies):
    ws_url = "wss://demo.traccar.org/api/socket"
    ws = create_connection(ws_url, header=[f"Cookie: {cookies.get('JSESSIONID')}"])
    print("Conectado ao WebSocket para monitoramento em tempo real!")

    try:
        while True:
            resultado = ws.recv()
            dados = json.loads(resultado)

            if 'positions' in dados:
                for posicao in dados['positions']:
                    lat = posicao['latitude']
                    lon = posicao['longitude']
                    device_id = posicao['deviceId']
                    
                    # Verificar se o dispositivo está na rota
                    na_rota = verificar_rota((lat, lon))
                    
                    status_rota = "na rota" if na_rota else "fora da rota"
                    print(f"Dispositivo ID {device_id} está em {lat}, {lon} - {status_rota}")
    except KeyboardInterrupt:
        print("Monitoramento encerrado.")
    finally:
        ws.close()

# Execução do código
if __name__ == "__main__":
    try:
        cookies = autenticar_traccar()
        dispositivos = obter_dispositivos(cookies)
        print(f"Dispositivos encontrados: {[dispositivo['name'] for dispositivo in dispositivos]}")

        # Iniciar monitoramento em tempo real
        monitorar_em_tempo_real(cookies)

    except Exception as e:
        print("Erro: ", e)
