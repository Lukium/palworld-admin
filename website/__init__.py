""" The main module for the website. """

import io
import json
import logging
from mimetypes import guess_type
import os
import uuid

from flask import (
    Flask,
    Response,
    abort,
    send_file,
    redirect,
    url_for,
    flash,
    render_template,
    session,
    request,
)

from waitress import serve

from settings import app_settings
from converter.convert import convert_json_to_sav

from .views import create_views


# Serve the Flask app with Waitress
def flask_app():
    """Run the Flask app with Waitress."""
    app = create_app()
    serve(app, host="0.0.0.0", port=8210)


def create_app():
    """Create the Flask app."""

    if not app_settings.dev:
        app = Flask(__name__, static_folder=None)
    else:
        app = Flask(__name__)

    views = create_views()
    app.register_blueprint(views, url_prefix="/")

    app.secret_key = uuid.uuid4().hex

    if not app_settings.dev:
        # Serve the templates from memory that were downloaded from the remote server
        app.jinja_loader = app_settings.memorystorage.template_loader

        # Serve the static files from memory that were downloaded from the remote server
        @app.route("/static/<path:filename>")
        def static(filename):
            """Serve static files from memory."""
            file_path = f"/static/{filename}"
            logging.info("Requested static file: %s", file_path)
            if file_path in app_settings.memorystorage.static_files_in_memory:
                content = app_settings.memorystorage.static_files_in_memory[
                    file_path
                ]
                # Use the mimetypes module to guess the correct MIME type
                mimetype, _ = guess_type(filename)
                mimetype = mimetype or "application/octet-stream"
                return Response(content, mimetype=mimetype)
            else:
                abort(404)

    if app_settings.localserver.management_mode == "remote":

        @app.route("/login", methods=["GET", "POST"])
        def login():
            """Render the login page."""
            webview_headers = session.get("webview_headers", None)
            management_mode = session.get("management_mode", None)
            if request.method == "POST":
                if (
                    request.form["password"]
                    == app_settings.localserver.management_password
                ):
                    session["authenticated"] = True
                    return redirect(url_for("views.server_installer"))
                else:
                    flash("Incorrect password. Please try again.")
            return render_template(
                "login.html",
                webview_headers=webview_headers,
                management_mode=management_mode,
                version=app_settings.version,
            )  # Ensure you have a login.html template

        @app.route("/logout")
        def logout():
            """Log the user out and redirect to the login page."""
            session.pop(
                "authenticated", None
            )  # Remove 'authenticated' from session
            return redirect(url_for("login"))

    @app.route("/generate_sav", methods=["POST"])
    def generate_sav():
        """Generate WorldOption.sav and return it as a file download."""
        # Generate WorldOption.sav.json and convert it to WorldOption.sav
        properties_data = {
            "Settings": {
                "struct_type": "PalOptionWorldSettings",
                "struct_id": "00000000-0000-0000-0000-000000000000",
                "id": None,
                "value": {},
                "type": "StructProperty",
            }
        }

        for (
            key,
            default_value,
        ) in app_settings.palworldsettings_defaults.default_values.items():
            submitted_value = request.form.get(key, default_value)
            if str(submitted_value) != str(default_value):
                if submitted_value.lower() in ["true", "false"]:
                    value = (
                        True if submitted_value.lower() == "true" else False
                    )
                    _type = "BoolProperty"
                elif submitted_value.replace(".", "", 1).isdigit():
                    value = (
                        float(submitted_value)
                        if "." in submitted_value
                        else int(submitted_value)
                    )
                    _type = (
                        "FloatProperty"
                        if "." in submitted_value
                        else "IntProperty"
                    )
                else:
                    value = submitted_value
                    _type = "StrProperty"

                properties_data["Settings"]["value"][key] = {
                    "id": None,
                    "value": value,
                    "type": _type,
                }

        json_data = {
            "header": {
                "magic": 1396790855,
                "save_game_version": 3,
                "package_file_version_ue4": 522,
                "package_file_version_ue5": 1008,
                "engine_version_major": 5,
                "engine_version_minor": 1,
                "engine_version_patch": 1,
                "engine_version_changelist": 0,
                "engine_version_branch": "++UE5+Release-5.1",
                "custom_version_format": 3,
                "custom_versions": [
                    ["40d2fba7-4b48-4ce5-b038-5a75884e499e", 7],
                    ["fcf57afa-5076-4283-b9a9-e658ffa02d32", 76],
                    ["0925477b-763d-4001-9d91-d6730b75b411", 1],
                    ["4288211b-4548-16c6-1a76-67b2507a2a00", 1],
                    ["1ab9cecc-0000-6913-0000-4875203d51fb", 100],
                    ["4cef9221-470e-d43a-7e60-3d8c16995726", 1],
                    ["e2717c7e-52f5-44d3-950c-5340b315035e", 7],
                    ["11310aed-2e55-4d61-af67-9aa3c5a1082c", 17],
                    ["a7820cfb-20a7-4359-8c54-2c149623cf50", 21],
                    ["f6dfbb78-bb50-a0e4-4018-b84d60cbaf23", 2],
                    ["24bb7af3-5646-4f83-1f2f-2dc249ad96ff", 5],
                    ["76a52329-0923-45b5-98ae-d841cf2f6ad8", 5],
                    ["5fbc6907-55c8-40ae-8e67-f1845efff13f", 1],
                    ["82e77c4e-3323-43a5-b46b-13c597310df3", 0],
                    ["0ffcf66c-1190-4899-b160-9cf84a46475e", 1],
                    ["9c54d522-a826-4fbe-9421-074661b482d0", 44],
                    ["b0d832e4-1f89-4f0d-accf-7eb736fd4aa2", 10],
                    ["e1c64328-a22c-4d53-a36c-8e866417bd8c", 0],
                    ["375ec13c-06e4-48fb-b500-84f0262a717e", 4],
                    ["e4b068ed-f494-42e9-a231-da0b2e46bb41", 40],
                    ["cffc743f-43b0-4480-9391-14df171d2073", 37],
                    ["b02b49b5-bb20-44e9-a304-32b752e40360", 3],
                    ["a4e4105c-59a1-49b5-a7c5-40c4547edfee", 0],
                    ["39c831c9-5ae6-47dc-9a44-9c173e1c8e7c", 0],
                    ["78f01b33-ebea-4f98-b9b4-84eaccb95aa2", 20],
                    ["6631380f-2d4d-43e0-8009-cf276956a95a", 0],
                    ["12f88b9f-8875-4afc-a67c-d90c383abd29", 45],
                    ["7b5ae74c-d270-4c10-a958-57980b212a5a", 13],
                    ["d7296918-1dd6-4bdd-9de2-64a83cc13884", 3],
                    ["c2a15278-bfe7-4afe-6c17-90ff531df755", 1],
                    ["6eaca3d4-40ec-4cc1-b786-8bed09428fc5", 3],
                    ["29e575dd-e0a3-4627-9d10-d276232cdcea", 17],
                    ["af43a65d-7fd3-4947-9873-3e8ed9c1bb05", 15],
                    ["6b266cec-1ec7-4b8f-a30b-e4d90942fc07", 1],
                    ["0df73d61-a23f-47ea-b727-89e90c41499a", 1],
                    ["601d1886-ac64-4f84-aa16-d3de0deac7d6", 80],
                    ["5b4c06b7-2463-4af8-805b-bf70cdf5d0dd", 10],
                    ["e7086368-6b23-4c58-8439-1b7016265e91", 4],
                    ["9dffbcd6-494f-0158-e221-12823c92a888", 10],
                    ["f2aed0ac-9afe-416f-8664-aa7ffa26d6fc", 1],
                    ["174f1f0b-b4c6-45a5-b13f-2ee8d0fb917d", 10],
                    ["35f94a83-e258-406c-a318-09f59610247c", 41],
                    ["b68fc16e-8b1b-42e2-b453-215c058844fe", 1],
                    ["b2e18506-4273-cfc2-a54e-f4bb758bba07", 1],
                    ["64f58936-fd1b-42ba-ba96-7289d5d0fa4e", 1],
                    ["697dd581-e64f-41ab-aa4a-51ecbeb7b628", 88],
                    ["d89b5e42-24bd-4d46-8412-aca8df641779", 41],
                    ["59da5d52-1232-4948-b878-597870b8e98b", 8],
                    ["26075a32-730f-4708-88e9-8c32f1599d05", 0],
                    ["6f0ed827-a609-4895-9c91-998d90180ea4", 2],
                    ["30d58be3-95ea-4282-a6e3-b159d8ebb06a", 1],
                    ["717f9ee7-e9b0-493a-88b3-91321b388107", 16],
                    ["430c4d19-7154-4970-8769-9b69df90b0e5", 15],
                    ["aafe32bd-5395-4c14-b66a-5e251032d1dd", 1],
                    ["23afe18e-4ce1-4e58-8d61-c252b953beb7", 11],
                    ["a462b7ea-f499-4e3a-99c1-ec1f8224e1b2", 4],
                    ["2eb5fdbd-01ac-4d10-8136-f38f3393a5da", 5],
                    ["509d354f-f6e6-492f-a749-85b2073c631c", 0],
                    ["b6e31b1c-d29f-11ec-857e-9f856f9970e2", 1],
                    ["4a56eb40-10f5-11dc-92d3-347eb2c96ae7", 2],
                    ["d78a4a00-e858-4697-baa8-19b5487d46b4", 18],
                    ["5579f886-933a-4c1f-83ba-087b6361b92f", 2],
                    ["612fbe52-da53-400b-910d-4f919fb1857c", 1],
                    ["a4237a36-caea-41c9-8fa2-18f858681bf3", 5],
                    ["804e3f75-7088-4b49-a4d6-8c063c7eb6dc", 5],
                    ["1ed048f4-2f2e-4c68-89d0-53a4f18f102d", 1],
                    ["fb680af2-59ef-4ba3-baa8-19b573c8443d", 2],
                    ["9950b70e-b41a-4e17-bbcc-fa0d57817fd6", 1],
                    ["ab965196-45d8-08fc-b7d7-228d78ad569e", 1],
                ],
                "save_game_class_name": "/Script/Pal.PalWorldOptionSaveGame",
            },
            "properties": {
                "Version": {"id": None, "value": 100, "type": "IntProperty"},
                "OptionWorldData": {
                    "struct_type": "PalOptionWorldSaveData",
                    "struct_id": "00000000-0000-0000-0000-000000000000",
                    "id": None,
                    "value": properties_data,
                    "type": "StructProperty",
                },
            },
            "trailer": "AAAAAA==",
        }

        # Save the JSON data to a file named 'WorldOption.sav.json'
        with open(
            os.path.join("./", "WorldOption.sav.json"), "w", encoding="utf-8"
        ) as json_file:
            json.dump(json_data, json_file, indent=2)

        # Check if WorldOption.sav exists and delete it
        if os.path.exists("WorldOption.sav"):
            os.remove("WorldOption.sav")

        # Run convert.py with the saved file as an argument
        # subprocess.run(["python3", "convert.py", "WorldOption.sav.json"])
        convert_json_to_sav("WorldOption.sav.json", "WorldOption.sav")

        # Load WorldOption.sav into memory
        with open("WorldOption.sav", "rb") as sav_file:
            sav_data = io.BytesIO(sav_file.read())

        # Delete the file from the filesystem
        os.remove("WorldOption.sav")
        os.remove("WorldOption.sav.json")

        # Set the filename for the file-like object
        sav_data.seek(0)
        return send_file(
            sav_data,
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name="WorldOption.sav",
        )

    return app
