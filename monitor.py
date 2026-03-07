import requests
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from datetime import datetime

# Configurações dos Servidores FiveM
SERVERS = {
    "r76lgj": "Rua2",
    "ameby5": "Bloodlines",
    "89vpk5": "BHRP"
}
API_URL = "https://servers-frontend.fivem.net/api/servers/single/{}"

# Configuração InfluxDB (via Environment Variables)
INFLUX_URL = os.getenv('INFLUX_URL')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET')

def fetch_server_data():
    """Busca dados de todos os servidores FiveM"""
    all_points = []
    
    for server_id, server_name in SERVERS.items():
        try:
            response = requests.get(f"{API_URL.format(server_id)}", timeout=10)
            data = response.json()
            
            online = data.get('online', 0)
            max_players = data.get('max', 0)
            
            # Cria ponto para InfluxDB
            point = Point("fivem_players") \
                .tag("server_name", server_name) \
                .tag("server_id", server_id) \
                .field("online", online) \
                .field("max", max_players) \
                .time(datetime.utcnow(), write_precision='s')
            
            all_points.append(point)
            print(f"[{server_name}] Online: {online}/{max_players}")
            
        except Exception as e:
            print(f"❌ Erro ao buscar {server_name}: {e}")
    
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
        write_api.write(bucket=INFLUX_BUCKET, record=points)
        client.close()
        print(f"✅ {len(points)} pontos enviados para InfluxDB")
    except Exception as e:
        print(f"❌ Erro ao enviar para InfluxDB: {e}")

if __name__ == '__main__':
    print("🚀 Iniciando monitoramento FiveM...")
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    points = fetch_server_data()
    push_to_influxdb(points)
    
    print("✅ Monitoramento concluído")