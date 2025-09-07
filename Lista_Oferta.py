import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

import extractDataOferta

import json

import os
import random

import json
from datetime import datetime

from data import logger

OFERTAS_SEMESTRE = None
SEMESTRE_ATUAL = None
ANO_ATUAL = None
NOME_ARQUIVO = ""

def obter_ano_e_semestre_personalizado():
    """
    Retorna um JSON com o ano e o semestre com base em uma regra específica.

    Regra de Semestre:
    - 1º semestre: De Novembro a Abril.
    - 2º semestre: De Maio a Outubro.

    O ano no resultado corresponde ao ano em que o semestre letivo termina.
    """
    data_atual = datetime.now()
    mes_atual = data_atual.month
    ano_atual = data_atual.year

    ano_do_semestre = ano_atual
    semestre = 0

    # Verifica se o mês atual peERRORS_TOTALrtence ao 2º semestre (Maio a Outubro)
    if 5 <= mes_atual <= 10:
        semestre = 2
        ano_do_semestre = ano_atual
    # Caso contrário, pertence ao 1º semestre (Novembro a Abril)
    else:
        semestre = 1
    # Se for Novembro ou Dezembro, o semestre termina no ano seguinte
    if mes_atual >= 11:
        ano_do_semestre = ano_atual + 1
    # Se for de Janeiro a Abril, o semestre termina no ano atual
    else:
        ano_do_semestre = ano_atual

    # Cria o dicionário com o resultado
    resultado = {
        "ano": ano_do_semestre,
        "semestre": semestre
    }

    # Retorna o dicionário convertido para uma string JSON formatada
    return resultado



###################################################################################################################


def click(wait, xpath, text=None):
    try:
        elemento_xpath = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elemento_xpath.click()

        if (text != None):
            elemento_xpath.clear()
            elemento_xpath.send_keys(text)
    except:
        print("Houve um erro ao clicar no botão: ", xpath)
        logger.error("Houve um erro ao clicar no botão: ", xpath)




def extractOferta():
    OFERT = {}

    TimeOutWebDriverMaxOferta = 10
    NivelDeEnsino_Xpath = '//*[@id="formTurma:inputNivel"]'
    Depto_Xpath = '//*[@id="formTurma:inputDepto"]'
    BotaoBusca_Xpath = '//*[@id="formTurma"]/table/tfoot/tr/td/input[1]'
    xapth_tbody = '//*[@id="turmasAbertas"]/table/tbody'


    ###################################################################################
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ativa o modo headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')

    service = Service(log_path='NUL')

    navegador = webdriver.Chrome(service=service, options=chrome_options)

    wait = WebDriverWait(navegador, TimeOutWebDriverMaxOferta)
    ####################################################################################


    navegador.get("https://sigaa.unb.br/sigaa/public/turmas/listar.jsf?aba=p-ensino")

    time.sleep(10)
    click(wait, '//*[@id="sigaa-cookie-consent"]/button') #clicar em aceitar cookies

    #definir semestre
    global SEMESTRE_ATUAL
    semestre = SEMESTRE_ATUAL
    click(wait, '//*[@id="formTurma:inputPeriodo"]')
    click(wait, f'//*[@id="formTurma:inputPeriodo"]/option[{semestre}]')
    click(wait, '//*[@id="formTurma:inputAno"]', "2025")



    select_element_ensino = Select(navegador.find_element(By.XPATH, NivelDeEnsino_Xpath))
    #Itera sobre "Nivel de ensino"
    for index_ensino in range(1, len(select_element_ensino.options)):         
        select_element_ensino = Select(navegador.find_element(By.XPATH, NivelDeEnsino_Xpath))
        select_element_ensino.select_by_index(index_ensino)

        opcao_selecionada_ensino = select_element_ensino.first_selected_option.text
        print("Opção Maior: ", opcao_selecionada_ensino)
        if ("GRAD" not in opcao_selecionada_ensino.upper()):
            print("Não é graduação, pulando for")
            continue

        select_element_depto = Select(navegador.find_element(By.XPATH, Depto_Xpath))

        #Itera sobre departamento
        for index_depto in range(1, len(select_element_depto.options)):
            select_element_depto = Select(navegador.find_element(By.XPATH, Depto_Xpath))
            select_element_depto.select_by_index(index_depto)

            click(wait, BotaoBusca_Xpath)
            
            time.sleep(5)
            if ("Não foram encontrados resultados para a busca com estes parâmetros" in navegador.page_source):
                continue

            try:
                elementLista = navegador.find_element(By.XPATH, xapth_tbody)
                elementLista_html = elementLista.get_attribute("outerHTML")
                
                CacheData = extractDataOferta.extractData(elementLista_html)
                OFERT.update(CacheData)
                time.sleep(5)
            except Exception as e:
                print("Terminando a execuao por provemas")
                logger.error("Erro ao extrair dados da oferta: ", e)
                return

    navegador.quit()

    
    global NOME_ARQUIVO
    logger.info(f"Gerando arquivo de oferta: {NOME_ARQUIVO}")
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as arquivo:
        json.dump(OFERT, arquivo, ensure_ascii=False, indent=4)
    logger.info(f"Arquivo de oferta {NOME_ARQUIVO} gerado com sucesso")

    global OFERTAS_SEMESTRE
    OFERTAS_SEMESTRE = OFERT

    OFERT = {}
    return



def verifyMateria(codDisciplina:str, horario:str, professor:str):
    codDisciplina = codDisciplina.upper()
    codDisciplina = codDisciplina.strip()
    professor = professor.upper()
    professor = professor.strip()
    horario = horario.upper()
    while ("  " in horario): horario = horario.replace("  ", " ")
    for i in range(2):
        if (i==1):
            if (" " in horario): 
                horario = horario.replace(" ", "  ")
                print("segundo if")
            else :
                continue

        horario = horario.strip()

        print ("HORARIO", horario)
        global OFERTAS_SEMESTRE
        if (OFERTAS_SEMESTRE == None):
            print("Carregando ofertas da memoria")
            with open("oferta.json", "r", encoding="utf-8") as arquivo:
                OFERTAS_SEMESTRE = json.load(arquivo)


        if codDisciplina not in OFERTAS_SEMESTRE:
            return False
        
        if (professor != "" and horario != ""):
            for chave, info in OFERTAS_SEMESTRE[codDisciplina].items():
                if chave.startswith('Turma'):
                    if (professor.upper() in str(info.get('Professor')).upper()) and (info.get('Horario') == horario):
                        turma_numero = chave.replace("Turma", "").strip()
                        data = {
                            "codigo": codDisciplina,
                            "Nome_disciplina": OFERTAS_SEMESTRE[codDisciplina]["Nome da Disciplina"],
                            "Turma": turma_numero,
                            "Professor": normalizarNomeProf(info.get('Professor')),
                            "Horario": info.get('Horario')
                        }
                        return data
                    
        elif (professor == "" and horario == ''):
            for chave, info in OFERTAS_SEMESTRE[codDisciplina].items():
                data = {
                    "codigo": codDisciplina,
                    "Nome_disciplina": OFERTAS_SEMESTRE[codDisciplina]["Nome da Disciplina"],
                    "Professor": "",
                    "Horario": ""
                }
                return data
        elif (professor == "" and horario != ''):
            list_turmas = ""
            for chave, info in OFERTAS_SEMESTRE[codDisciplina].items():
                if chave.startswith('Turma'):
                    if (info.get('Horario') == horario):
                        turma_numero = chave.replace("Turma", "").strip()
                        list_turmas += f", {turma_numero}"
                        horario = info.get('Horario')

            if (list_turmas == ''): continue

            if (list_turmas[0] == ","): list_turmas = list_turmas[1:].strip()
            data = {
                "codigo": codDisciplina,
                "Nome_disciplina": OFERTAS_SEMESTRE[codDisciplina]["Nome da Disciplina"],
                "Professor": "",
                "Turma": list_turmas,
                "Horario": horario
            }
            print("Data: ", data)  
            return data
        
        elif (professor != "" and horario == ''):
            list_turmas = ""
            for chave, info in OFERTAS_SEMESTRE[codDisciplina].items():
                if chave.startswith('Turma'):
                    if (professor in str(info.get('Professor'))):
                        turma_numero = chave.replace("Turma", "").strip()
                        list_turmas += f", {turma_numero}"
    
            if (list_turmas == ''): continue

            if (list_turmas[0] == ","): list_turmas = list_turmas[1:].strip()
            data = {
                "codigo": codDisciplina,
                "Nome_disciplina": OFERTAS_SEMESTRE[codDisciplina]["Nome da Disciplina"],
                "Professor": professor,
                "Turma": list_turmas,
                "Horario": ""
            }
            return data
    
    return False


def normalizarNomeProf(nome):
    # Encontrar a posição da primeira ocorrência da letra "e"
    pos_e = nome.find("e")
    
    # Se "e" for encontrado, retorne a substring até essa posição
    if pos_e != -1:
        return nome[:pos_e].strip()  # Usando strip() para remover espaços extras
    else:
        return nome  # Caso a letra "e" não seja encontrada, retorna o nome completo



def readControlThread(nome_arquivo='control.json'):
    with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
            return dados
def setControlThread(dados={"controleTrhead":False}, nome_arquivo='control.json'):
    with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)    



def main():
    tempo_aleatorio = random.uniform(0, 10)
    time.sleep(tempo_aleatorio)
    tempo_aleatorio = random.uniform(0, 3)
    time.sleep(tempo_aleatorio)

    controle = bool(readControlThread().get("controleTrhead"))
    if (controle == False):
        print("Thread de oferta desativada no control.json")
        return
    setControlThread()

    global SEMESTRE_ATUAL, ANO_ATUAL, NOME_ARQUIVO
    while True:
        try:
            SEMESTRE_ATUAL = int(obter_ano_e_semestre_personalizado()["semestre"])
            ANO_ATUAL = int(obter_ano_e_semestre_personalizado()["ano"])
            NOME_ARQUIVO = f'ofertas/oferta_{ANO_ATUAL}_{SEMESTRE_ATUAL}.json'
            
            print("Semestre Atual: ", SEMESTRE_ATUAL)
            print("Ano Atual: ", ANO_ATUAL)
            
            logger.info(f"Iniciando Extração de Oferta de Matérias | Semestre: {SEMESTRE_ATUAL} | Ano: {ANO_ATUAL}")
            extractOferta()
            logger.info(f"Terminada Extração de Oferta de Matérias | Semestre: {SEMESTRE_ATUAL} | Ano: {ANO_ATUAL}")
            print("Terminada Extração de Oferta de Matérias")
        except Exception as e:
            print("Erro na catalogação de lista de oferta: ", e)
            logger.error("Erro na catalogação de lista de oferta: ", e)
        time.sleep(43200)  # Repete a execução a cada 12 horas

