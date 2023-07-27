import numpy as np
import torch, os, json, io, cv2, time
from ultralytics import YOLO
from PIL import Image
import requests

def model_fn(model_dir):
    print("Executing model_fn from inference.py ...")
    env = os.environ
    model = YOLO("/opt/ml/model/code/" + env['YOLOV8_MODEL'])
    return model

def input_fn(request_body, request_content_type):
    print("Executing input_fn from inference.py ...")
    if request_content_type.lower() == "image/png" or request_content_type.lower() == "image/jpg" or request_content_type.lower() == "image/jpeg":
        # jpg_original = np.load(io.BytesIO(request_body), allow_pickle=True)
        # jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
        # img = cv2.imdecode(jpg_as_np, flags=-1)
        image = Image.open(io.BytesIO(request_body))
        image = np.asarray(image)
        return image        
    elif request_content_type.lower() == "application/jsonlines" or request_content_type.lower == "application/jsonlines":
        # request_body = b'{"image_url":"https://www.addictivetips.com/app/uploads/2017/10/ios-privacy-settings.jpg"}'    
        print("request_body:")
        print(request_body)
        request_body_fix_single_quotes = request_body.replace(b"'", b'"')
        print("request_body_fix_single_quotes:")
        print(request_body_fix_single_quotes)
        request_body_json = json.load(io.BytesIO(request_body_fix_single_quotes))
        print("request_body_json:")
        print(request_body_json)
        image_url = request_body_json['image_url']    
        print("image_url:")
        print(image_url)
        response = requests.get(image_url)
        image = Image.open(io.BytesIO(response.content))
        image = np.asarray(image)
        return image        
    else:
        raise Exception("Unsupported content type: " + request_content_type)
    
def predict_fn(input_data, model):
    print("Executing predict_fn from inference.py ...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    with torch.no_grad():
        result = model(input_data, imgsz=1760)
    return result
        
def output_fn(prediction_output, content_type):
    print("Executing output_fn from inference.py ...")
    # YOLO can handle multiple images, get predictions for first image
    results_for_first_image = prediction_output[0]

    # Create empty NumPy array
    rows, cols = 0, 5
    predictions = np.empty((rows, cols))

    # Iterate through predictions
    for result in results_for_first_image:
        # Get box from object and convert from TensorFlow to NumPy array
        box = result.boxes[0].numpy()
        # Get label class from object
        # this gets added as a Float because the NumPy array can only have one data type
        cls = box.cls        
        # Extract coordinates (first row)
        coordinates = box.xywhn[0, :]
        # Stitch coordinates and label calls together in one array
        prediction = np.append(cls, coordinates)
        # Append prediction to multi row array
        print(prediction)
        predictions = np.vstack((predictions, prediction))    
    return json.dumps(predictions.tolist())