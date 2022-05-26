import argparse
import json
import os

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote


SCIENCE_FICTION_CATEGORY_URL = "https://tululu.org/l55/{page}/"
DOWNLOAD_URL = "https://tululu.org/txt.php"


def parse_book_page(book_url):
    response = requests.get(book_url)
    response.raise_for_status()
    page_code = BeautifulSoup(response.text, "lxml")

    header_tag = page_code.select_one("h1").text
    book_name, author_name = header_tag.split(" :: ")

    img_selector = "div.bookimage img"
    img_url = urljoin(book_url, page_code.select_one(img_selector)["src"])
    id_and_ext = urlsplit(img_url).path.split("/")[-1]

    genre_tag_selector = "span.d_book a"
    book_genre_tags = page_code.select(genre_tag_selector)
    book_genres = [genre_tag.text for genre_tag in book_genre_tags]

    comments_selector = "div.texts span.black"
    comments = page_code.select(comments_selector)
    comments_texts = [comment.text for comment in comments]

    book_parameters = {
        "name": book_name.strip(),
        "author": author_name.strip(),
        "img_url": img_url,
        "img_id": id_and_ext,
        "genre": book_genres,
        "comments": comments_texts
    }
    return book_parameters


def download_image(id, folder):
    response = requests.get(id)
    response.raise_for_status()

    filename = urlsplit(id).path.split("/")[-1]
    filepath = os.path.join(folder, filename)
    with open(unquote(filepath), "wb") as file:
        file.write(response.content)
    return f"Картинка: {filepath}"


def download_book(download_url, params, filename, folder="books/"):
    response = requests.get(download_url, params=params)
    response.raise_for_status()

    filepath = os.path.join(folder, f"{sanitize_filename(filename)}.txt")
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(response.text)
    return f"Книга: {filepath}"


def get_books_urls_from_category(category_url, start_page, end_page):
    books_urls = []

    for page in range(start_page, end_page):
        response = requests.get(category_url.format(page=page))
        page_code = BeautifulSoup(response.text, "lxml")

        books_selector = "table.d_book"
        books = page_code.select(books_selector)
        
        for book in books:
            books_urls.append(urljoin(category_url.format(page=page), book.find("a")["href"]))
    return books_urls


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Программа скачивает книги, обложки, сохраняет описание в JSON."
    )
    parser.add_argument(
        "--start_page",
        type=int,
        help="С какой книги скачать",
        default=1
    )
    parser.add_argument(
        "--end_page",
        type=int,
        help="До какой книги скачать",
        default=5
    )
    parser.add_argument(
        "--dest_folder",
        help="Путь к каталогу с результатами парсинга",
        default="media"
    )
    parser.add_argument(
        "--skip_imgs",
        action="store_true",
        help="Не скачивать картинки"
    )
    parser.add_argument(
        "--skip_txt",
        action="store_true",
        help="Не скачивать книги"
    )
    parser.add_argument(
        "--json_path",
        help="Путь к JSON файлу с информацией о книгах",
        default="media"
    )
    args = parser.parse_args()

    imgs_dir = f"./E-book-web/{args.dest_folder}/images"
    books_dir = f"./E-book-web/{args.dest_folder}/books"
    json_path = f"./E-book-web/{args.json_path}/books.json"

    os.makedirs(imgs_dir, exist_ok=True)
    os.makedirs(books_dir, exist_ok=True)

    books_parameters = []

    for book_url in get_books_urls_from_category(
        SCIENCE_FICTION_CATEGORY_URL,
        args.start_page,
        args.end_page
    ):
        params = {"id": book_url.split("https://tululu.org/b")[1].split("/")[0]}

        book_page = parse_book_page(book_url)
        books_parameters.append(book_page)
        if not args.skip_imgs:
            download_image(book_page["img_url"], folder=imgs_dir)
        if not args.skip_txt:
            download_book(
                DOWNLOAD_URL,
                params,
                book_page["name"],
                folder=books_dir
            )

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(books_parameters, file, ensure_ascii=False)
