import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXIT_ERROR_LOCK = 1
EXIT_ERROR_CORRUPT_DB = 2
EXIT_SUCCESS = 0

DB_CONFIG = "config"
DB_LANG = "lang"
DB_SCHEMA = "schema"
DB_STRUCT = "structure"
DB_USERS = "users"
DB_SERVER = "server"
DB_BASE = "base"
DB_SECRET = "secret"
DB_MODULE = "module"
DB_ALERT = "alert"

RUNNING_STATUS = "running"
STOPPED_STATUS = "stopped"
UNKNOWN_STATUS = "unknown"


KEY_MONITOR_ZABBIX_ID = "monitor.zabbix.id"
KEY_MONITOR_NB_CPU = "nbcpu"
KEY_MONITOR_HISTORY = "history"
KEY_MONITOR_LISTS = "lists"
KEY_MONITOR_MEMORY = "memory"
KEY_MONITOR_DISK = "disk"
KEY_MONITOR_CPU_USAGE = "cpuUsage"
KEY_MONITOR_MOUNTS = "mounts"

KEY_DISCOVER_PROXMOX_ID = "discover.proxmox.id"
KEY_DISCOVER_PROXMOX_STATUS = "discover.proxmox.status"

KEY_SSH_USER = "ssh.user"
KEY_SSH_PASSWORD = "ssh.password"
KEY_SSH_PORT = "ssh.port"

KEY_TYPE = "type"
KEY_NET_IP = "net.ip"
KEY_NET_ETH = "net.eth"
KEY_NET_MAC = "net.mac"

KEY_NAME = "name"

KEY_LAST_UPDATE = "lastUpdate"
KEY_MONITOR = "monitor"
KEY_HYPERVISOR = "hypervisor"
KEY_STATUS = "status"

KEY_TUNNEL_IP = "tunnel.ip"
KEY_TUNNEL_USER = "tunnel.user"
KEY_TUNNEL_PASSWORD = "tunnel.password"
KEY_TUNNEL_PORT = "tunnel.port"
KEY_TUNNEL_NETWORK = "tunnel.network"
CRYPTO_KEY_ENCRYPTION = "ZnyBnKI7N/ETSqSq+HgnIZ4f4TvrHMYV"
DEBUG = False
