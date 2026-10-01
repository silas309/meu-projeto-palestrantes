import os
import re
import sqlite3
import requests
from urllib.parse import urljoin

# Constantes e Configurações
URL_PAGINA = "https://eventos.ifgoiano.edu.br/integra2026/"
ARQUIVO_TXT = "pagina_fonte.txt"
PASTA_DOWNLOAD = "downloads"
BANCO_DADOS = "event.db"

# ==============================================================================
# TAREFA 002: Baixar código-fonte e salvar em arquivo TXT
# ==============================================================================
def tarefa_002_baixar_html():
    print("[Tarefa 002] Baixando código-fonte da página...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(URL_PAGINA, headers=headers)
    response.raise_for_status()
    
    with open(ARQUIVO_TXT, "w", encoding="utf-8") as file:
        file.write(response.text)
    print(f"-> Código-fonte salvo em '{ARQUIVO_TXT}'.")

# ==============================================================================
# TAREFA 003: Extrair dados usando Expressões Regulares (re)
# ==============================================================================
def tarefa_003_extrair_dados():
    print("[Tarefa 003] Extraindo dados com Expressões Regulares...")
    
    with open(ARQUIVO_TXT, "r", encoding="utf-8") as file:
        conteudo = file.read()

    # Expressão regular ajustada para capturar os blocos de modal e cartão de cada palestrante
    # Padrão extrai: URL da imagem, Nome, Local de Trabalho e E-mail de contato
    padrao = re.compile(
        r'<img[^>]+src=["\'](?P<imagem>[^"\']+)["\'][^>]*>.*?<h5[^>]*>(?P<nome>.*?)</h5>\s*<p[^>]*>(?P<trabalho>.*?)</p>.*?<p[^>]*>(?P<email>[\w\.-]+@[\w\.-]+\.\w+)</p>',
        re.DOTALL | re.IGNORECASE
    )

    palestrantes = []
    
    # Alternativa modular baseada nas tags identificadas no documento (id="PalestranteX" e modalX)
    blocos = re.findall(r'id=["\']Palestrante\d+["\'].*?</div>\s*</div>\s*</div>', conteudo, re.DOTALL)
    
    if not blocos:
        # Busca genérica caso o HTML mude de formato
        matches = padrao.finditer(conteudo)
        for match in matches:
            palestrantes.append({
                'imagem': match.group('imagem').strip(),
                'nome': match.group('nome').strip(),
                'trabalho': match.group('trabalho').strip(),
                'email': match.group('email').strip()
            })
    else:
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

    print(f"-> Total de palestrantes encontrados: {len(palestrantes)}")
    return palestrantes

# ==============================================================================
# TAREFA 004: Baixar imagens para a pasta 'downloads'
# ==============================================================================
def tarefa_004_baixar_imagens(palestrantes):
    print("[Tarefa 004] Baixando imagens dos palestrantes...")
    if not os.path.exists(PASTA_DOWNLOAD):
        os.makedirs(PASTA_DOWNLOAD)

    for item in palestrantes:
        rel_url = item['imagem']
        full_url = urljoin(URL_PAGINA, rel_url)
        
        nome_arquivo = os.path.basename(rel_url)
        caminho_local = os.path.join(PASTA_DOWNLOAD, nome_arquivo)

        # Atualiza a referência de imagem para salvar apenas o nome do arquivo no banco
        item['nome_imagem_local'] = nome_arquivo

        try:
            res = requests.get(full_url, stream=True)
            if res.status_code == 200:
                with open(caminho_local, 'wb') as f:
                    for chunk in res.iter_content(1024):
                        f.write(chunk)
        except Exception as e:
            print(f"Erro ao baixar a imagem {nome_arquivo}: {e}")

    print(f"-> Imagens salvas com sucesso no diretório '{PASTA_DOWNLOAD}'.")

# ==============================================================================
# TAREFA 005 & 006: Criar Banco de Dados SQLite e Inserir Registros
# ==============================================================================
def tarefa_005_e_006_salvar_no_banco(palestrantes):
    print("[Tarefa 005 & 006] Inicializando o banco SQLite e salvando dados...")
    
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()

    # Criação da tabela 'speaker' conforme a especificação
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS speaker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            work VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            image VARCHAR(255) NOT NULL
        )
    ''')

    # Limpa registros antigos para evitar duplicatas em re-execuções
    cursor.execute("DELETE FROM speaker")

    # Inserção de dados
    for p in palestrantes:
        cursor.execute('''
            INSERT INTO speaker (name, work, email, image)
            VALUES (?, ?, ?, ?)
        ''', (p['nome'], p['trabalho'], p['email'], p['nome_imagem_local']))

    conn.commit()
    conn.close()
    print(f"-> Registros salvos na tabela 'speaker' em '{BANCO_DADOS}'.")

# ==============================================================================
# Execução Principal
# ==============================================================================
if __name__ == "__main__":
    tarefa_002_baixar_html()
    dados_palestrantes = tarefa_003_extrair_dados()
    
    if dados_palestrantes:
        tarefa_004_baixar_imagens(dados_palestrantes)
        tarefa_005_e_006_salvar_no_banco(dados_palestrantes)
        print("\nProcesso concluído com sucesso!")
    else:
        print("\nNenhum palestrante foi extraído. Verifique o HTML retornado.")
