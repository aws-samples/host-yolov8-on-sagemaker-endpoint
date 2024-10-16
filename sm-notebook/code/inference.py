import numpy as np
import torch, os, json, base64, cv2, time
from ultralytics import YOLO

def model_fn(model_dir):
    print("Executing model_fn from inference.py ...")
    env = os.environ
    model = YOLO(os.path.join(model_dir, env['YOLOV8_MODEL']))
    return model

def input_fn(request_body, request_content_type):
    print("Executing input_fn from inference.py ...")
    if request_content_type:
        jpg_original = base64.b64decode(request_body)
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
    for result in prediction_output:
        if 'boxes' in result._keys and result.boxes is not None:
            infer['boxes'] = result.boxes.cpu().numpy().data.tolist()
        if 'masks' in result._keys and result.masks is not None:
            infer['masks'] = result.masks.cpu().numpy().data.tolist()
        if 'keypoints' in result._keys and result.keypoints is not None:
            infer['keypoints'] = result.keypoints.cpu().numpy().data.tolist()
        if 'probs' in result._keys and result.probs is not None:
            infer['probs'] = result.probs.cpu().numpy().data.tolist()
    return json.dumps(infer)