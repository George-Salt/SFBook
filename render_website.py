import json
import math
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def render_page(books, name, pages_quantity):
    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("./template.html")

    rendered_page = template.render(
        books=books,
        pages_num=pages_quantity,
        index=name
    )

    with open(f"./pages/index{name}.html", "w", encoding="utf8") as file:
        file.write(rendered_page)


def on_reload(books_by_pages, pages_num):
    for index, page in enumerate(books_by_pages):
        render_page(page, index, pages_num)
    print("Site rebuilt")


if __name__ == "__main__":
    os.makedirs("./pages", exist_ok=True)

    books_on_page = 10
    pair = 2
    pairs_on_page = 5

    with open("./media/books.json", "r", encoding="utf8") as file:
        books = json.load(file)

    books_by_pages = list(chunked(list(chunked(books, pair)), pairs_on_page))

    pages_num = math.ceil(len(books) / books_on_page)

    for index, page in enumerate(books_by_pages):
        render_page(page, index, pages_num)

    server = Server()
    server.watch("./template.html", on_reload(books_by_pages, pages_num))
    server.serve(root=".")
