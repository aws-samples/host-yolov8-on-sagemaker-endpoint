import numpy as np
import torch, os, json, io, cv2, time
from ultralytics import YOLO

def model_fn(model_dir):
    print("Executing model_fn from inference.py ...")
    env = os.environ
    model = YOLO("/opt/ml/model/code/" + env['YOLOV8_MODEL'])
    return model

def input_fn(request_body, request_content_type):
    print("Executing input_fn from inference.py ...")
    if request_content_type:
        jpg_original = np.load(io.BytesIO(request_body), allow_pickle=True)
        jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
        img = cv2.imdecode(jpg_as_np, flags=-1)
    else:
        raise Exception("Unsupported content type: " + request_content_type)
    return img
    
def predict_fn(input_data, model):
    print("Executing predict_fn from inference.py ...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    with torch.no_grad():
        result = model(input_data)
    return result
        
def output_fn(prediction_output, content_type):
    print("Executing output_fn from inference.py ...")
    infer = {}
    image_no = 0
    for result in prediction_output:
        path = str(image_no)
        if hasattr(result,'path'):
            path = result.path
        infer[path] = {}
        if hasattr(result, 'boxes'):
            if result.boxes:
                infer[path]['boxes_xyxy'] = result.boxes.xyxy.tolist()
                infer[path]['boxes_xywh'] = result.boxes.xywh.tolist()
                infer[path]['boxes_xyxyn'] = result.boxes.xyxyn.tolist()
                infer[path]['boxes_xywhn'] = result.boxes.xywhn.tolist()
                infer[path]['confidence'] = result.boxes.conf.tolist()
        if hasattr(result, 'masks'):
            infer[path]['masks'] = {}
            if result.masks:
                infer[path]['masks'] = result.masks.tolist()
        if hasattr(result, 'keypoints'):
            infer[path]['keypoints'] = {}
            if result.keypoints:
                infer[path]['keypoints'] = result.keypoints.tolist()
        if hasattr(result, 'probs'):
            infer[path]['probs'] = {}
            if result.probs:
                infer[path]['probs'] = result.probs.tolist()
        image_no += 1
    return json.dumps(infer)