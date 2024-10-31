import os
import sys
import json
import subprocess
from text_parser.text_parser import parse,is_valid
from diagram_parser.parser import diagram_parser
from diagram_parser.detection.test import detect_image
from theorem_predict.tools.demo_generate_random_seqs import seq_gen_demo
from theorem_predict.demo_eval_transformer import bart_demo
import cv2
from tqdm import tqdm
from multiprocess import Pool
import glob
from diagram_parser.ocr_tool import mathpix
import time
import random
from numpy.random import seed

seed(1234)
random.seed(1234)

OUTPUT_FILE_TEXT = 'output/text/text_logic_forms.json'
OUTPUT_FILE_DIAGRAM = 'output/diagram/diagram_logic_forms.json'

def parse_text_and_diagram():
    with open('input/data.json', 'r') as f:
        data = json.load(f)
    input_text = data['compact_text']
    input_text
    pid = 'input_diagram'
    logic_forms, output_text, reduced_text = parse(input_text)
    logic_valid = is_valid(logic_forms)
    if logic_valid and len(reduced_text) < 4:
        success = True
        print("Parse Successfully")
    else:
        success = False
        print("Parse Failed")
    output_data = {}
    output_data[pid] = {}
    output_data[pid]["text_logic_forms"] = logic_forms
    output_data[pid]["output_text"] = output_text
    output_data[pid]["success"] = success
    print("Saving results to {}".format(OUTPUT_FILE_TEXT))
    os.makedirs(os.path.dirname(OUTPUT_FILE_TEXT), exist_ok=True)
    with open(OUTPUT_FILE_TEXT, 'w') as f:
        json.dump(output_data, f, indent = 2, separators=(',', ': '))

    input_image = "input"
    detect_model = "diagram_parser\detection\models\csv_retinanet_100.pt"
    class_list = "diagram_parser\detection\classes.txt"
    output_path = "output\diagram"
    detect_image(input_image, detect_model,class_list,output_path)
    folder = 'output\diagram\ocr_results'
    # folder = 'output\\test'
    sub_folders = os.listdir(folder)

    for sub_folder in sub_folders:
        files = os.listdir(os.path.join(folder, sub_folder))
        files = list(filter(lambda x: x.endswith('jpg'), files))
        
        for file in files:
            path = os.path.join(folder, sub_folder, file)
            r = mathpix.latex({
                'src': mathpix.image_uri(path),
                'formats': ['latex_simplified']
            })
            res = json.dumps(r, indent=4, sort_keys=True)
            # print(res['latex_simplified'])

            id = os.path.splitext(file)[0]
            print(r)
            with open(os.path.join(folder, sub_folder, id+'.json'), 'w') as f:
                f.write(res)
            print(os.path.join(folder, sub_folder, id+'.json'))
            
            time.sleep(1.5)

    data_path = "input/text/data.json"
    ocr_path = "output/diagram/ocr_results"
    box_path = "output/diagram/box_results"
    output_path = OUTPUT_FILE_DIAGRAM
    detection_id = ['input_diagram']
    box_id = detection_id[0]
    data_id = box_id
    ocr_results, sign_results, size_results = diagram_parser.load_symbol(detection_id, ocr_path, box_path)
    para_lst = []
    json_file = data_path
    with open(json_file, 'r') as f:
        data = json.load(f)
    diagram_path = ('input\diagram\input_diagram.png')
    img = cv2.imread(diagram_path)
    factor = (1, 1)
    if size_results[box_id] is not None:
        factor = (img.shape[1] / size_results[box_id][1], img.shape[0] / size_results[box_id][0])
    para_lst.append((data_id, box_id, ocr_results[box_id], sign_results[box_id], data, img, factor))
    solve_list = []
    with tqdm(total=len(para_lst), ncols=80) as t:
        with Pool(10) as p:
            for answer in p.imap_unordered(diagram_parser.multithread_solve, para_lst):
                solve_list.append(answer)
                t.update()
    solve_list = sorted(solve_list, key=lambda x: x['id'])
    final = {}
    for entry in solve_list:
        id = entry["id"]
        del entry["id"]
        final[id] = entry
    with open(output_path, "w") as f:
        json.dump(final, f, indent = 2)


# Hàm để xóa tất cả các tệp tin trong một thư mục
def delete_files_in_directory(directory):
    files = glob.glob(os.path.join(directory, '*'))
    for f in files:
        try:
            os.remove(f)
            print(f"Deleted file: {f}")
        except OSError as e:
            print(f"Error deleting file {f}: {e}")

def solve():
    seq_gen_demo()
    bart_demo()
    input_file = 'output\demo\pred_seqs_test_bart_best.json'
    output_file = 'output\demo\pred_seqs_test_bart_best_random.json'
    input = json.load(open(input_file))

    output = {}
    for pid, data in input.items():
        new_seq = data['seq'][0] + random.sample(list(range(1,18))*10, 100)
        output[pid] = {'id':pid, 'num_seqs':1, 'seq':new_seq}
        
    ## Save result.json file
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, separators=(',', ': '))
    venv_python = sys.executable
    command = [
        venv_python, 'symbolic_solver/demo_test.py',
        '--data_path', 'input/data.json',
        '--label', 'final_new',
        '--strategy', 'final',
        '--text_logic_form_path', 'output/text/text_logic_forms.json',
        '--diagram_logic_form_path', 'output/diagram/diagram_logic_forms.json',
        '--predict_path', 'output/demo/pred_seqs_test_bart_best.json'
    ]
    # Thực hiện lệnh
    result = subprocess.run(command, capture_output=True, text=True)
    
    # In ra kết quả
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    print("Return code:", result.returncode)

def edit_file():
    # Đọc dữ liệu từ file JSON thứ nhất
    with open('output/logic_form_edited.json', 'r') as file:
        edited_data = json.load(file)
    # Đọc dữ liệu từ file JSON thứ hai và ba
    with open('output/text/text_logic_forms.json', 'r') as file:
        text = json.load(file)

    with open('output/diagram/diagram_logic_forms.json', 'r') as file:
        diagram = json.load(file)

    # Hàm để thay thế các giá trị của trường trong đối tượng JSON
    def replace_values(source, target):
        for key, value in source.items():
            if key in target['input_diagram']:
                # print(key)
                if isinstance(value, dict) and isinstance(target['input_diagram'][key], dict):
                    target['input_diagram'][key] = value 
                else:
                    target['input_diagram'][key] = value

    # Thay thế các giá trị trong text_data nếu tồn tại trong edit_data
    replace_values(edited_data, text)

    # Thay thế các giá trị trong diagram_data nếu tồn tại trong edit_data
    replace_values(edited_data, diagram)

    # Ghi dữ liệu đã thay thế vào file text_updated.json và diagram_updated.json
    with open('output/text/text_logic_forms.json', 'w', encoding='utf-8') as file:
        json.dump(text, file, ensure_ascii=False, indent=4)

    with open('output/diagram/diagram_logic_forms.json', 'w', encoding='utf-8') as file:
        json.dump(diagram, file, ensure_ascii=False, indent=4)