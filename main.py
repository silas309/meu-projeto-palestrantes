import os
import re
import sqlite3
import requests
from urllib.parse import urljoin

URL_PAGINA = "https://eventos.ifgoiano.edu.br/integra2026/"
ARQUIVO_TXT = "pagina_fonte.txt"
PASTA_DOWNLOAD = "downloads"
BANCO_DADOS = "event.db"

def tarefa_002_baixar_html():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(URL_PAGINA, headers=headers)
    response.raise_for_status()
    with open(ARQUIVO_TXT, "w", encoding="utf-8") as file:
        file.write(response.text)

def tarefa_003_extrair_dados():
    with open(ARQUIVO_TXT, "r", encoding="utf-8") as file:
        conteudo = file.read()
    
    palestrantes = []
    blocos = re.findall(r'id=["\']Palestrante\d+["\'].*?</div>\s*</div>\s*</div>', conteudo, re.DOTALL)
    
    for bloco in blocos:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', bloco)
        nome_match = re.search(r'<h5[^>]*>(.*?)</h5>', bloco)
        trabalho_match = re.search(r'</h5>\s*<p[^>]*>(.*?)</p>', bloco, re.DOTALL)
        email_match = re.search(r'([\w\.-]+@[\w\.-]+\.\w+)', bloco)

        if img_match and nome_match and trabalho_match and email_match:
            palestrantes.append({
                'imagem': img_match.group(1).strip(),
                'nome': nome_match.group(1).strip(),
                'trabalho': trabalho_match.group(1).strip(),
                'email': email_match.group(1).strip()
            })
    return palestrantes

def tarefa_004_baixar_imagens(palestrantes):
    if not os.path.exists(PASTA_DOWNLOAD):
        os.makedirs(PASTA_DOWNLOAD)

    for item in palestrantes:
        rel_url = item['imagem']
        full_url = urljoin(URL_PAGINA, rel_url)
        nome_arquivo = os.path.basename(rel_url)
        caminho_local = os.path.join(PASTA_DOWNLOAD, nome_arquivo)
        item['nome_imagem_local'] = nome_arquivo

        try:
            res = requests.get(full_url, stream=True)
            if res.status_code == 200:
                with open(caminho_local, 'wb') as f:
                    for chunk in res.iter_content(1024):
                        f.write(chunk)
        except Exception as e:
            pass

def tarefa_005_e_006_salvar_no_banco(palestrantes):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS speaker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            work VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            image VARCHAR(255) NOT NULL
        )
    ''')
    cursor.execute("DELETE FROM speaker")
    for p in palestrantes:
        cursor.execute('''
            INSERT INTO speaker (name, work, email, image)
            VALUES (?, ?, ?, ?)
        ''', (p['nome'], p['trabalho'], p['email'], p['nome_imagem_local']))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    tarefa_002_baixar_html()
    dados = tarefa_003_extrair_dados()
    if dados:
        tarefa_004_baixar_imagens(dados)
        tarefa_005_e_006_salvar_no_banco(dados)