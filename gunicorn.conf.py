# gunicorn.conf.py
import json

def when_ready(server):
    dados = {"controleTrhead":True}
    with open("control.json", 'w', encoding='utf-8') as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)  


# O número de processos de trabalho.
# (2 * n_cores) + 1 é uma boa regra.
workers = 4

preload_app = True

# O endereço e a porta para vincular.
# '0.0.0.0' torna o servidor acessível de qualquer IP na rede.
bind = "0.0.0.0:5002"

# Nível de log. Opções: 'debug', 'info', 'warning', 'error', 'critical'
loglevel = "info"

#rodar com gunicorn -c gunicorn.conf.py app_oferta:app