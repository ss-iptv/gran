import os
import requests
import time
import urllib.parse
from dotenv import load_dotenv


load_dotenv()

URL_PACOTE = os.getenv("URL_PACOTE")
ID_PACOTE = os.getenv("ID_PACOTE")
URL_CURSO = os.getenv("URL_CURSO")
BEARER = os.getenv("BEARER")


def main():
    if not URL_PACOTE or not ID_PACOTE or not URL_CURSO or not BEARER:
        print("Preencha corretamente as variáveis de ambiente! (.env)")
        return

    countdown()
    handle_folders()
    process_pacote()

    print("\n\nProcessamento Finalizado!")


def handle_folders():
    if not os.path.exists("estrategia"):
        os.mkdir("estrategia")
    with open("errors.txt", "w") as file:
        file.write(f"")


def process_pacote():
    response = request_json(f"{URL_PACOTE}{ID_PACOTE}")
    pacote = response["data"]
    nome_pacote = pacote["nome"]
    cursos = pacote["cursos"]
    prefix = create_folder("estrategia/", nome_pacote)
    handle_cursos(cursos, prefix)


def handle_cursos(cursos, prefix):
    for curso in cursos:
        id_curso = curso["id"]
        nome_curso = curso["nome"]
        new_prefix = create_folder(prefix, nome_curso)

        response = request_json(f"{URL_CURSO}{id_curso}")
        curso_data = response["data"]
        aulas = curso_data["aulas"]
        handle_aulas(aulas, new_prefix)


def handle_aulas(aulas, prefix):
    for aula in aulas:
        nome_aula = aula["nome"]
        url_pdf = aula["pdf"]
        nome_pdf = aula["conteudo"]
        new_prefix = create_folder(prefix, nome_aula)

        if url_pdf is None or not pdf_exists(new_prefix, nome_pdf):
            continue

        pdf_response = request_pdf(url_pdf)
        if not pdf_response is None:
            save_pdf(pdf_response, new_prefix, nome_pdf)
            print(f"PDF {new_prefix} - salvo!\n\n")


def countdown():
    print("Iniciando processamento em (Aperte ctrl + c para parar):")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print("Processamento iniciado!")


def pdf_exists(path, filename):
    filename = handle_illegal_characters(filename)
    return os.path.exists(path + filename + ".pdf")


def request_json(url):
    try:
        headers = {"Authorization": f"Bearer {BEARER}"}
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        with open("errors.txt", "a") as file:
            file.write(f"{url} - {e}\n")
        return []


def request_pdf(url):
    try:
        headers = {"Authorization": f"Bearer {BEARER}"}
        response = requests.get(url, headers=headers)
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
    if not os.path.exists(path):
        os.mkdir(path)
    return path + "/"


def handle_illegal_characters(value):
    illegal_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    return ("".join(c if c not in illegal_chars else " " for c in value))[:200]


def encode(value):
    return urllib.parse.quote(value, safe=" ")


if __name__ == "__main__":
    main()
