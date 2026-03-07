import requests
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from datetime import datetime
import json

# Configurações dos Servidores FiveM
SERVERS = {
    "r76lgj": "Rua2",
    "ameby5": "Bloodlines",
    "89vpk5": "BHRP"
}
API_URL = "https://servers-frontend.fivem.net/api/servers/single/{}"

# Configuração InfluxDB
INFLUX_URL = os.getenv('INFLUX_URL')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET')

def fetch_server_data():
    """Busca dados de todos os servidores FiveM"""
    all_points = []
    
    for server_id, server_name in SERVERS.items():
        try:
            print(f"\n📡 Consultando servidor: {server_name}")
            print(f"ID: {server_id}")
            
            url = API_URL.format(server_id)
            print(f"URL: {url}")
            
            headers = {
                'User-Agent': 'FiveM-Monitor/1.0',
                'Accept': 'application/json'
            }
            
            response = requests.get(
                url, 
                timeout=10,
                headers=headers
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Verificar se é JSON válido
            try:
                data = response.json()
                print(f"✅ JSON válido!")
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao parsear JSON: {e}")
                print(f"📦 Conteúdo bruto (primeiras 500 chars):")
                print(response.text[:500])
                continue
            
            # Verificar quais campos existem
            print(f"🔍 Campos disponíveis: {list(data.keys())}")
            
            # CAMPOS CORRETOS DA API
            if 'Data' in data:
                clients = data['Data'].get('clients', 0)
                max_clients = data['Data'].get('sv_maxclients', 0) or data['Data'].get('svMaxclients', 0)
            else:
                # Fallback para estrutura antiga
                clients = data.get('online', 0)
                max_clients = data.get('max', 0)
            
            print(f"✅ Clients: {clients} | Max Clients: {max_clients}")
            
            # Cria ponto para InfluxDB
            point = Point("fivem_players") \
                .tag("server_name", server_name) \
                .tag("server_id", server_id) \
                .field("clients", clients) \
                .field("max_clients", max_clients) \
                .time(datetime.utcnow(), write_precision='s')
            
            all_points.append(point)
            
        except Exception as e:
            print(f"❌ Erro ao buscar {server_name}: {e}\n {response.text()} \n {response.status_code()}")
            import traceback
            traceback.print_exc()
        
        # Delay entre requisições para evitar rate limiting
        time.sleep(2)
    
    return all_points

def push_to_influxdb(points):
    """Envia dados para InfluxDB"""
    if not points:
        print("⚠️ Nenhum dado para enviar")
        return
    
    try:
        client = InfluxDBClient(
            url=INFLUX_URL, 
            token=INFLUX_TOKEN, 
            org=INFLUX_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        print(f"\n📤 Enviando {len(points)} pontos para InfluxDB...")
        write_api.write(bucket=INFLUX_BUCKET, record=points)
        client.close()
        print(f"✅ {len(points)} pontos enviados com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar para InfluxDB: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🚀 Iniciando monitoramento FiveM...")
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Configuração: Bucket={INFLUX_BUCKET}, Org={INFLUX_ORG}")
    
    points = fetch_server_data()
    push_to_influxdb(points)
    
    print("\n✅ Monitoramento concluído")
