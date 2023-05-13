import os
import requests
from http.cookiejar import CookieJar
import time
import shutil
import urllib.parse
from dotenv import load_dotenv


def countdown():
    print("Iniciando processamento em (Aperte ctrl + c para parar):")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print("Processamento iniciado!")


def handle_folders():
    if os.path.exists("content"):
        shutil.rmtree("content")
    os.mkdir("content")
    with open("errors.txt", "w") as file:
        file.write(f"")


def setAuthCookie():
    cookie = requests.cookies.create_cookie(name=COOKIE_NAME, value=COOKIE_VALUE)
    cookie_jar.set_cookie(cookie)


def encode(value):
    return urllib.parse.quote(value, safe=" ")


def requestFile(download_type, fk, aula_name):
    fk_encoded = encode(fk)
    url = URL_AULAS.replace("DOWNLOAD_TYPE", download_type).replace(
        "FK_ENCODED", fk_encoded
    )
    retry_count = 0
    retry_limit = 3

    while retry_count < retry_limit:
        response = requests.get(url, cookies=cookie_jar)
        if response.status_code == 200 and len(response.content) > 0:
            return response.content
        else:
            print(f"Erro em {url}, tentando novamente...")
            time.sleep(1)
            retry_count += 1

    with open("errors.txt", "a") as file:
        file.write(f"\nErro ao baixar {download_type} de {aula_name} em {url}")
    print(f"Não foi possível baixar {url} depois de {retry_limit} tentativas.")
    return bytearray()


def handle_illegal_characters(value):
    illegal_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    return "".join(c if c not in illegal_chars else "_" for c in value)


def saveFile(content, disciplina_name, aula_name, filename):
    aula_name = handle_illegal_characters(aula_name)
    disciplina_name = handle_illegal_characters(disciplina_name)

    disciplina_path = f"content/{disciplina_name}"
    aula_path = f"{disciplina_path}/{aula_name}"

    if not os.path.exists(disciplina_path):
        os.mkdir(disciplina_path)

    if not os.path.exists(aula_path):
        os.mkdir(aula_path)

    with open(os.path.join(aula_path, filename + ".pdf"), "wb") as f:
        f.write(content)


def handle_aulas(aulas, disciplina_name):
    count = 1
    for aula in aulas:
        aula_name = f"{count} {aula['st_titulo_novo']}"
        fk_apostila = aula["fk_apostila"]
        fk_resumo = aula["fk_material_resumo"]

        if fk_apostila:
            pdfContent = requestFile("apostila", fk_apostila, aula_name)
            saveFile(pdfContent, disciplina_name, aula_name, "slide")

        if fk_resumo:
            pdfContent = requestFile("resumo", fk_resumo, aula_name)
            saveFile(pdfContent, disciplina_name, aula_name, "resumo")

        print(f"{disciplina_name} - {aula_name} salvo!\n")
        count = count + 1


def handle_disciplinas(disciplinas):
    for disciplina in disciplinas:
        disciplina_id = disciplina["id"]
        disciplina_name = disciplina["nome"]

        url = URL_DISCIPLINA.replace("CURSO_ID", CURSO_ID).replace(
            "DISCIPLINA_ID", disciplina_id
        )
        response = requests.get(url, cookies=cookie_jar)

        aulas = response.json()
        handle_aulas(aulas, disciplina_name)


def get_disciplinas():
    url = URL_CURSO.replace("CURSO_ID", CURSO_ID)
    response = requests.get(url, cookies=cookie_jar)
    return response.json()


def main():
    countdown()
    handle_folders()
    setAuthCookie()
    disciplinas = get_disciplinas()
    handle_disciplinas(disciplinas)
    print("Processamento finalizado!")


cookie_jar = CookieJar()
load_dotenv()
CURSO_ID = os.getenv("CURSO_ID")
URL_CURSO = os.getenv("URL_CURSO")
URL_DISCIPLINA = os.getenv("URL_DISCIPLINA")
URL_AULAS = os.getenv("URL_AULAS")
COOKIE_NAME = os.getenv("COOKIE_NAME")
COOKIE_VALUE = os.getenv("COOKIE_VALUE")

if __name__ == "__main__":
    main()
