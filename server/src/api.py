import os
import json

from storage import storage

from flask import (
    Blueprint, request, send_from_directory
)

bp = Blueprint('auth', __name__, url_prefix='/api')


@bp.route("/documents/<doc_name>")
def get_page(doc_name):
    page = request.args.get('page', default="1", type=int)
    print(page)

    return f"get page {doc_name} {page}"


@bp.route("/documents/<doc_name>/pdf")
def get_document_pdf(doc_name):
    filename = f"{doc_name}.pdf"

    return send_from_directory(storage.pdf_dir, filename)


@bp.route("/documents/<doc_name>/predictions")
def get_document_predictions(doc_name):
    data_dir = storage.get_json_path(doc_name)
    pages = os.listdir(data_dir)
    result = []
    for page in pages:
        with open(data_dir / page) as f:
            data = json.load(f)
            data = {k: data[k] for k in data.keys() if not k.startswith("_")}
            result.append(data)

    return result


@bp.route("/documents/<doc_name>/pages/<int:page>/predictions")
def get_page_predictions(doc_name, page):
    data_dir = storage.get_json_path(doc_name)
    with open(data_dir / f"page{page}.json") as f:
        data = json.load(f)
        result = {k: data[k] for k in data.keys() if k != '_image'}

    return result
