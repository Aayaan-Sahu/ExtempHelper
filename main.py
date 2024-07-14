import flask
import pickle
from utils import Url, setup_models, generate_information, search
from datetime import datetime

model, embd_model, prompt = setup_models()

app = flask.Flask("ExtempWizard")


try:
    with open("index.bin", "rb") as handler:
        index = pickle.load(handler)
except FileNotFoundError:
    print("File not found, starting from blank")
    index = []


@app.route("/")
def route_index():
    response = flask.make_response(flask.render_template("index.html", index=index))

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@app.route("/search", methods=["POST"])
def route_search():
    data = flask.request.get_json(force=True)
    sorted_links_information = search(data["query"], index, embd_model)
    return flask.jsonify(sorted_links_information)


@app.route("/summary", methods=["POST"])
def return_summary():
    data = flask.request.get_json(force=True)
    title_to_search = data["article_title"]
    for entry in index:
        if entry["title"] == title_to_search:
            return flask.jsonify(entry["summary"])
    return flask.jsonify(title_to_search)


@app.route("/new", methods=["POST"])
def route_new():
    data = flask.request.get_json(force=True)

    date = ""
    try:
        date = data["datetime"]
    except Exception as e:
        print("Could not find date. Returning following exception:", e)
        date = str(datetime.now().strftime("%m.%d.%y"))

    url = Url(data["title"], data["url"], date)
    generate_information(index, prompt, model, embd_model, url)
    with open("index.bin", "wb") as handler:
        pickle.dump(index, handler)
    return "done"


if __name__ == "__main__":
    app.run(debug=True, port=4000)
