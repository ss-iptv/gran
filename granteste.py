import os
import requests
from http.cookiejar import CookieJar
import time
import urllib.parse
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
cookie_jar = CookieJar()

# Define constants
CURSO_ID = os.getenv("CURSO_ID")
BASE_URL = os.getenv("BASE_URL")
DISCIPLINAS_URL = BASE_URL + os.getenv("DISCIPLINAS_URL").replace("CURSO_ID", CURSO_ID)
CONTEUDOS_URL = DISCIPLINAS_URL + os.getenv("CONTEUDOS_URL")
DOWNLOAD_AULA_URL = BASE_URL + os.getenv("DOWNLOAD_AULA_URL")
DISCIPLINAS_PDF_URL = BASE_URL + os.getenv("DISCIPLINAS_PDF_URL").replace("CURSO_ID", CURSO_ID)
CONTEUDOS_PDF_URL = DISCIPLINAS_PDF_URL + os.getenv("CONTEUDOS_PDF_URL")
DOWNLOAD_AULA_PDF_URL = BASE_URL + os.getenv("DOWNLOAD_AULA_PDF_URL")
AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME")
AUTH_COOKIE_VALUE = os.getenv("AUTH_COOKIE_VALUE")
ILLEGAL_CHARS = ["<", ">", ":", '"', "/", "\\", "|", "?", "*", "\0", ".", "-", "\t", "\n", "\r"]

# Define functions
def set_auth_cookie():
    cookie = requests.cookies.create_cookie(name=AUTH_COOKIE_NAME, value=AUTH_COOKIE_VALUE)
    cookie_jar.set_cookie(cookie)

def handle_folders(apagar):
    if apagar and os.path.exists("grancursos"):
        shutil.rmtree("grancursos")
    os.makedirs("grancursos", exist_ok=True)
    with open("errors.txt", "w") as file:
        file.write(f"")

def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")

def draw_menu():
    clear_terminal()
    print("|========= Automação Grancursos =========|")
    print("|                                        |")
    print("| Qual operação deseja realizar?         |")
    print("|  1. Download das aulas em PDF          |")
    print("|  2. Download de slides e degravações   |")
    print("|  3. Download de ambos                  |")
    print("|                                        |")
    print("|========================================|")

    while True:
        operacao = input("")
        if operacao in (1, 2, 3, "1", "2", "3"):
            break
        else:
            print("Opção inválida. Por favor, escolha uma opção válida.")

    clear_terminal()

    print("|========= Automação Grancursos =========|")
    print("|                                        |")
    print("| Deseja apagar os conteúdos anteriores? |")
    print("|  1. Sim                                |")
    print("|  2. Não                                |")
    print("|                                        |")
    print("|========================================|")

    while True:
        apagar = input("")
        if apagar in (1, 2, "1", "2"):
            break
        else:
            print("Opção inválida. Por favor, escolha uma opção válida.")

    clear_terminal()

    return int(operacao), int(apagar)

def countdown():
    print("Iniciando processamento em (Aperte ctrl + c para parar):")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print("Processamento iniciado!")

def process_disciplinas():
    print("\nIniciando download dos slides e degravações.")
    disciplinas = request_json(DISCIPLINAS_URL)
    handle_disciplinas(disciplinas, "Slides e Degravações", handle_aulas, CONTEUDOS_URL)
    print("Download dos slides e degravações concluído.")

def process_disciplinas_pdf():
    print("\nIniciando download das aulas em pdf.")
    disciplinas_pdf = request_json(DISCIPLINAS_PDF_URL)
    handle_disciplinas(disciplinas_pdf, "Aulas em PDF", handle_aulas_pdf, CONTEUDOS_PDF_URL)
    print("Download das aulas em pdf concluído.")

def handle_disciplinas(disciplinas, path, callback_aulas, base_url):
    new_prefix = create_folder("grancursos/", path)

    for disciplina in disciplinas:
        disciplina_id = disciplina["id"]
        disciplina_name = disciplina["nome"]

        new_prefix_disciplina = create_folder(new_prefix, disciplina_name)
        url = base_url.replace("DISCIPLINA_ID", disciplina_id)
        conteudos = request_json(url)
        if conteudos:
            handle_conteudos(url, new_prefix_disciplina, conteudos, callback_aulas)

def handle_conteudos(url, prefix, conteudos, callback_aulas):
    count = 1
    for conteudo in conteudos:
        new_prefix = create_folder(prefix, f"Aula {count}")
        count += 1

        aulas = request_json(f"{url}{conteudo['id']}")
        if aulas:
            callback_aulas(new_prefix, aulas)

def handle_aulas(prefix, aulas):
    count = 1
    for aula in aulas:
        fk_apostila = aula["fk_apostila"]
        fk_resumo = aula["fk_material_resumo"]
        aula_name = f"{count} {aula['st_titulo_novo']}"
        count += 1
        new_prefix = create_folder(prefix, aula_name)
        handle_slide_or_resumo(fk_apostila, new_prefix, "slide")
        handle_slide_or_resumo(fk_resumo, new_prefix, "resumo")
        print("\n\n")

def handle_slide_or_resumo(fk, path, type_name):
    if fk and not pdf_exists(path, type_name):
        url = DOWNLOAD_AULA_URL.replace("TYPE", type_name).replace("FK", encode(fk))
        pdfContent = request_pdf(url)
        save_pdf(pdfContent, path, type_name)
        print(f"{path}{type_name}.pdf salvo!")
    else:
        print(f"{path}{type_name}.pdf já existe!")

def handle_aulas_pdf(prefix, aulas_pdf):
    count = 1
    for aula_pdf in aulas_pdf:
        aula_pdf_id = encode(aula_pdf["id_aula_pdf"])
        aula_pdf_name = f"{count} {aula_pdf['st_titulo']}"
        count += 1

        if pdf_exists(prefix, aula_pdf_name):
            print(f"{prefix}{aula_pdf_name} - já existe!\n\n")
            continue

        url = DOWNLOAD_AULA_PDF_URL.replace("AULA_PDF_ID", aula_pdf_id)
        pdf = request_pdf(url)
        save_pdf(pdf, prefix, aula_pdf_name)
        print(f"{prefix}{aula_pdf_name} - salvo!\n\n")

def pdf_exists(path, filename):
    filename = handle_illegal_characters(filename)
    return os.path.exists(path + filename + ".pdf")

def request_json(url):
    try:
        response = requests.get(url, cookies=cookie_jar)
        return response.json()
    except Exception as e:
        with open("errors.txt", "a") as file:
            file.write(f"{url} - {e}\n")
        return []

def request_pdf(url):
    try:
        response = requests.get(url, cookies=cookie_jar)
        return response.content
    except Exception as e:
        with open("errors.txt", "a") as file:
            file.write(f"{url} - {e}\n")
        return bytearray

def save_pdf(pdf, path, filename):
    filename = handle_illegal_characters(filename)
    with open(os.path.join(path, filename + ".pdf"), "wb") as f:
        f.write(pdf)

def create_folder(prefix, path):
    path = prefix + handle_illegal_characters(path)
    os.makedirs(path, exist_ok=True)
    return path + "/"

def handle_illegal_characters(value):
    return "".join(c if c not in illegal_chars else " " for c in value)


def encode(value):
    return urllib.parse.quote(value, safe=" ")


if __name__ == "__main__":
    main()
