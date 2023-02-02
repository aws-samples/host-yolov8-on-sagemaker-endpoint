import numpy as np
import torch, os, json, io, cv2, time
from ultralytics import YOLO

def model_fn(model_dir):
    print("-------- model fn --------")
    model = YOLO("/opt/ml/model/code/yolov8l.pt")
    return model

def input_fn(request_body, request_content_type):
    print(request_content_type)
    if request_content_type:
        jpg_original = np.load(io.BytesIO(request_body), allow_pickle=True)
        jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
        img = cv2.imdecode(jpg_as_np, flags=-1)
    else:
        raise Exception("Unsupported content type: " + request_content_type)
    return img
    
def predict_fn(input_data, model):
    print("-------- predict fn --------")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    with torch.no_grad():
        result = model(input_data)
    return result
        
def output_fn(prediction_output, content_type):
    print("-------- output fn --------")
    print(content_type)
    infer = {}
    for result in prediction_output:
        if result.boxes:
            infer['boxes'] = result.boxes.numpy().data.tolist()
        if result.masks:
            infer['masks'] = result.masks.numpy().data.tolist()
        if result.probs:
            infer['probs'] = result.probs.numpy().data.tolist()
    return json.dumps(infer)