import secrets

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.data import (
    export_json,
    export_toml,
    get_places_file,
    import_data,
    load_places,
    save_places,
)
from app.models import Place

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/about")
def about():
    return jsonify(
        {
            "name": "Food Picker",
            "description": "Randomly pick a place to eat from your personal list.",
            "repo": "https://github.com/ubahmapk/food-picker",
            "tech": ["Flask", "Pydantic", "Pico CSS", "Vanilla JS", "TOML"],
        }
    )


@api_bp.route("/categories", methods=["GET"])
def get_categories():
    places_file = get_places_file()
    data = load_places(places_file)
    return jsonify(data.categories)


@api_bp.route("/categories", methods=["POST"])
def add_category():
    places_file = get_places_file()
    data = load_places(places_file)

    payload = request.get_json() or {}
    name = payload.get("name", "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 422

    if name in data.categories:
        return jsonify({"error": "category already exists"}), 422

    data.categories.append(name)
    save_places(places_file, data)

    return jsonify(data.categories), 201


@api_bp.route("/categories/<name>", methods=["DELETE"])
def delete_category(name: str):
    places_file = get_places_file()
    data = load_places(places_file)

    if name not in data.categories:
        return jsonify({"error": "category not found"}), 404

    data.categories.remove(name)
    for place in data.places:
        if name in place.categories:
            place.categories = [c for c in place.categories if c != name]

    data.places = [p for p in data.places if p.categories]

    save_places(places_file, data)

    return jsonify({"status": "deleted"}), 200


@api_bp.route("/categories/<name>", methods=["PUT"])
def rename_category(name: str):
    places_file = get_places_file()
    data = load_places(places_file)

    if name not in data.categories:
        return jsonify({"error": "category not found"}), 404

    payload = request.get_json() or {}
    new_name = payload.get("name", "").strip()

    if not new_name:
        return jsonify({"error": "name is required"}), 422

    if new_name in data.categories and new_name != name:
        return jsonify({"error": "category already exists"}), 409

    data.categories = [new_name if c == name else c for c in data.categories]
    for place in data.places:
        place.categories = [new_name if c == name else c for c in place.categories]

    save_places(places_file, data)

    return jsonify({"name": new_name}), 200


@api_bp.route("/categories", methods=["PUT"])
def reorder_categories():
    places_file = get_places_file()
    data = load_places(places_file)

    payload = request.get_json() or {}
    categories = payload.get("categories", [])

    if not isinstance(categories, list):
        return jsonify({"error": "categories must be a list"}), 422

    if set(categories) != set(data.categories):
        return jsonify({"error": "category list mismatch"}), 422

    data.categories = categories
    save_places(places_file, data)

    return jsonify(data.categories), 200


@api_bp.route("/places", methods=["GET"])
def get_places():
    places_file = get_places_file()
    data = load_places(places_file)
    return jsonify([p.model_dump() for p in data.places])


@api_bp.route("/places", methods=["POST"])
def add_place():
    places_file = get_places_file()
    data = load_places(places_file)

    payload = request.get_json() or {}

    try:
        new_place = Place(**payload)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422

    if any(p.name == new_place.name for p in data.places):
        return jsonify({"error": "place already exists"}), 422

    for cat in new_place.categories:
        if cat not in data.categories:
            return jsonify({"error": f"category '{cat}' does not exist"}), 422

    data.places.append(new_place)
    save_places(places_file, data)

    return jsonify(new_place.model_dump()), 201


@api_bp.route("/places/<name>", methods=["DELETE"])
def delete_place(name: str):
    places_file = get_places_file()
    data = load_places(places_file)

    place = next((p for p in data.places if p.name == name), None)
    if not place:
        return jsonify({"error": "place not found"}), 404

    data.places = [p for p in data.places if p.name != name]
    save_places(places_file, data)

    return jsonify({"status": "deleted"}), 200


@api_bp.route("/places/<name>", methods=["PUT"])
def update_place(name: str):
    places_file = get_places_file()
    data = load_places(places_file)

    place = next((p for p in data.places if p.name == name), None)
    if not place:
        return jsonify({"error": "place not found"}), 404

    payload = request.get_json() or {}

    if "name" in payload:
        new_name = payload["name"].strip()
        if not new_name:
            return jsonify({"error": "name cannot be empty"}), 422
        if any(p.name == new_name and p.name != name for p in data.places):
            return jsonify({"error": "place already exists"}), 422
        place.name = new_name

    if "categories" in payload:
        cats = payload["categories"]
        if not isinstance(cats, list) or not cats:
            return jsonify({"error": "categories must be a non-empty list"}), 422
        for cat in cats:
            if cat not in data.categories:
                return jsonify({"error": f"category '{cat}' does not exist"}), 422
        place.categories = cats

    save_places(places_file, data)

    return jsonify(place.model_dump()), 200


@api_bp.route("/pick", methods=["GET"])
def pick():
    places_file = get_places_file()
    data = load_places(places_file)

    selected_categories = request.args.getlist("categories")
    vetoed = request.args.getlist("vetoed")

    if not selected_categories:
        selected_categories = data.categories

    pool = [
        p.name
        for p in data.places
        if any(cat in selected_categories for cat in p.categories) and p.name not in vetoed
    ]

    if not pool:
        return jsonify({"error": "no options remaining"}), 409

    choice = secrets.choice(pool)
    return jsonify({"name": choice}), 200


@api_bp.route("/export", methods=["GET"])
def export():
    places_file = get_places_file()
    data = load_places(places_file)

    fmt = request.args.get("format", "toml")

    if fmt == "json":
        content = export_json(data)
        filename = "places.json"
    elif fmt == "toml":
        content = export_toml(data)
        filename = "places.toml"
    else:
        return jsonify({"error": "unsupported format"}), 422

    return (
        content,
        200,
        {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/octet-stream",
        },
    )


@api_bp.route("/import", methods=["POST"])
def import_places():
    places_file = get_places_file()

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "file is required"}), 400

    filename = file.filename or ""
    if filename.endswith(".json"):
        fmt = "json"
    elif filename.endswith(".toml"):
        fmt = "toml"
    else:
        return jsonify({"error": "unsupported file type"}), 400

    try:
        raw = file.read()
        data = import_data(raw, fmt)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    save_places(places_file, data)

    return jsonify({"status": "imported"}), 200
