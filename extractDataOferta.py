from bs4 import BeautifulSoup
import re

def remover_ultimo_caractere(string):
    # Verifica se a string termina com " e"
    if string.endswith(" e"):
        # Remove os últimos 2 caracteres (o " e")
        return string[:-2]
    else:
        # Se não terminar com " e", retorna a string original
        return string
    
def extractData(html):
    listaMaterias = {}
    soup = BeautifulSoup(html, 'html.parser')

    # Encontra todas as linhas que definem o título da disciplina
    disciplinas = soup.find_all('tr', class_='agrupador')
    for disc in disciplinas:
        # Extrai o título completo (formato "Código - Nome")
        titulo_element = disc.find('span', class_='tituloDisciplina')
        if titulo_element:
            titulo_disciplina = titulo_element.get_text(strip=True)
            if " - " in titulo_disciplina:
                codigo, nome_disciplina = [x.strip() for x in titulo_disciplina.split(" - ", 1)]
            else:
                codigo = titulo_disciplina
                nome_disciplina = ""
            print("Código da Disciplina:", codigo)
            print("Nome da Disciplina:", nome_disciplina)
            if codigo not in listaMaterias:
                listaMaterias[codigo] = {}
                listaMaterias[codigo]["Nome da Disciplina"] = nome_disciplina
        # Busca as turmas relacionadas à disciplina (linhas seguintes com classe "linhaPar" ou "linhaImpar")
        turma_row = disc.find_next_sibling()
        while turma_row and any(cls in turma_row.get('class', []) for cls in ["linhaPar", "linhaImpar"]):
            # Número da turma
            numero_turma = turma_row.find('td', class_='turma').get_text(strip=True)
            
            # Nome do professor (removendo a carga horária, se existir)
            nome_professor_raw = turma_row.find('td', class_='nome').get_text(strip=True)
            nome_professor = re.sub(r'\(.*?\)', 'e ', nome_professor_raw).strip()
            nome_professor = remover_ultimo_caractere(nome_professor)
            
            # Extração do horário:
            # Consideramos o 4º <td> (índice 3) que contém o horário e removemos os elementos internos (img, span)
            tds = turma_row.find_all('td')
            if len(tds) > 3:
                horario_td = tds[3]
                for tag in horario_td.find_all(['img', 'span']):
                    tag.decompose()  # Remove os elementos filhos indesejados
                horario_text = horario_td.get_text(strip=True)
            else:
                horario_text = ""
            
            horario_text = re.sub(r'\(.*?\)', '', horario_text).strip()
            print("  Turma:", numero_turma)
            print("  Professor:", nome_professor)
            print("  Horário:", horario_text)
            print("----------")
            
            turma_row = turma_row.find_next_sibling()

            listaMaterias[codigo][f'Turma {numero_turma}'] = {
                "Professor": nome_professor,
                "Horario": horario_text
            }

    return listaMaterias