#!/usr/bin/env python
# coding: utf-8

import json
import ast
from tqdm import tqdm

import torch
from transformers import BartForConditionalGeneration, BartTokenizerFast


def evaluate(diagram_logic_file, text_logic_file, tokenizer_name, model_name, check_point, seq_num):

    ## read logic form files
    with open(diagram_logic_file) as f:
        diagram_logic_forms = json.load(f)
    with open(text_logic_file) as f:
        text_logic_forms = json.load(f)

    combined_logic_forms = {}

    pid = 'input_diagram'
    combined_logic_forms[pid] = diagram_logic_forms[pid]['diagram_logic_forms'] + \
                                text_logic_forms[pid]['text_logic_forms']

    ## build tokenizer and model
    tokenizer = BartTokenizerFast.from_pretrained(tokenizer_name) # 'facebook/bart-base'
    model = BartForConditionalGeneration.from_pretrained(model_name).to(device) # 'facebook/bart-base'
    model.load_state_dict(torch.load(check_point))

    final = dict()
    input = str(combined_logic_forms[pid])
    tmp = tokenizer.encode(input)
    if len(tmp) > 1024:
        tmp = tmp[:1024]
    input = torch.LongTensor(tmp).unsqueeze(0).to(device)

    output = model.generate(input, bos_token_id=0, eos_token_id=2,
                            max_length=20, num_beams=10, num_return_sequences=seq_num)
    # print(out.size())

    ## refine output sequence
    seq = []
    for j in range(seq_num):
        res = tokenizer.decode(output[j].tolist())
        res = res.replace("</s>", "").replace("<s>", "").replace("<pad>", "")
        res = '['+res
        # print(res)
        try:
            res = ast.literal_eval(res) # string class to list class
        except Exception as e:
            res = []
        seq.append(res)

    final[str(pid)] = {"id": str(pid), "num_seqs": seq_num, "seq": seq}

    return final

diagram_logic_file = 'output\diagram\diagram_logic_forms.json'
text_logic_file = 'output/text/text_logic_forms.json'

check_point = 'theorem_predict/models/tp_model_best.pt'
output_file = 'output/demo/pred_seqs_test_bart_best.json'

tokenizer_name = 'facebook/bart-base'
model_name = 'facebook/bart-base'

SEQ_NUM = 5

device = torch.device('cuda:0')

def bart_demo():
    result = evaluate(diagram_logic_file, text_logic_file, tokenizer_name, model_name, check_point, SEQ_NUM)
    with open(output_file, 'w') as f:
        json.dump(result, f)

