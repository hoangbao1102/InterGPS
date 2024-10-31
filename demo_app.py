from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import json
import os
from demo import parse_text_and_diagram,delete_files_in_directory,solve,edit_file

app = Flask(__name__)

# Configure upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'input'
app.config['DIAGRAM_FOLDER'] = 'output/diagram'
app.config['TEXT_FOLDER'] = 'output/text'
app.config['ALLOWED_EXTENSIONS'] = {'json', 'png', 'jpg', 'jpeg'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/parse_file', methods=['POST'])
def parse_file():
    if 'json_file' not in request.files or 'image_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    json_file = request.files['json_file']
    image_file = request.files['image_file']

    if json_file.filename == '' or image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not (allowed_file(json_file.filename) and allowed_file(image_file.filename)):
        return jsonify({'error': 'File type not allowed'}), 400

    json_filename = secure_filename(json_file.filename)
    image_filename = secure_filename(image_file.filename)

    json_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'data.json')
    image_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'input_diagram.png')

    json_file.save(json_filepath)
    image_file.save(image_filepath)

    box_results_dir = "output/diagram/box_results"
    ocr_results_dir = "output/diagram/ocr_results"

    delete_files_in_directory(box_results_dir)
    delete_files_in_directory(ocr_results_dir)

    parse_text_and_diagram()

    # Load the predefined JSON files
    diagram_json_path = os.path.join(app.config['DIAGRAM_FOLDER'], 'diagram_logic_forms.json')
    text_json_path = os.path.join(app.config['TEXT_FOLDER'], 'text_logic_forms.json')

    with open(diagram_json_path, 'r') as file:
        diagram_json_content = json.load(file)

    with open(text_json_path, 'r') as file:
        text_json_content = json.load(file)

    return jsonify({
        'diagram_logic_forms': diagram_json_content,
        'text_logic_forms': text_json_content
    })

@app.route('/json_solve', methods=['POST'])
def json_solve():
    if 'json_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    text_logic_file = request.files['json_file']

    if text_logic_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(text_logic_file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    text_logic_filename = secure_filename(text_logic_file.filename)

    text_logic_filepath = os.path.join('output', 'logic_form_edited.json')

    text_logic_file.save(text_logic_filepath)

    edit_file()

    solve()

    # Path to the predefined logic_input_diagram.json file
    logic_input_diagram_path = 'output/pred_results/logic_input_diagram.json'

    if not os.path.exists(logic_input_diagram_path):
        return jsonify({'error': 'logic_input_diagram.json not found'}), 404

    return send_file(logic_input_diagram_path, as_attachment=True)

@app.route('/main_solve', methods=['POST'])
def main_solve():
    if 'json_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    json_file = request.files['json_file']
    image_file = request.files['image_file']

    if json_file.filename == '' or image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not (allowed_file(json_file.filename) and allowed_file(image_file.filename)):
        return jsonify({'error': 'File type not allowed'}), 400

    json_filename = secure_filename(json_file.filename)
    image_filename = secure_filename(image_file.filename)

    json_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'data.json')
    image_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'input_diagram.png')

    json_file.save(json_filepath)
    image_file.save(image_filepath)

    box_results_dir = "output/diagram/box_results"
    ocr_results_dir = "output/diagram/ocr_results"

    delete_files_in_directory(box_results_dir)
    delete_files_in_directory(ocr_results_dir)

    parse_text_and_diagram()
    solve()

    # Path to the predefined logic_input_diagram.json file
    logic_input_diagram_path = 'output/pred_results/logic_input_diagram.json'

    if not os.path.exists(logic_input_diagram_path):
        return jsonify({'error': 'logic_input_diagram.json not found'}), 404

    return send_file(logic_input_diagram_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
