import cv2
import numpy as np

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Preprocess image for analysis"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Equalize histogram
    gray = cv2.equalizeHist(gray)
    
    # Normalize
    gray = gray.astype('float32') / 255.0
    
    return gray

def detect_faces(image: np.ndarray) -> List[tuple]:
    """Detect faces in image using Haar cascades"""
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    gray = preprocess_image(image)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    return faces