import cv2
import numpy as np
import base64
from PIL import Image
import io
import os

# Try importing face detection libraries, if available
try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False

try:
    from mtcnn import MTCNN
    MTCNN_AVAILABLE = True
except ImportError:
    MTCNN_AVAILABLE = False

class VideoAnalyzer:
    def __init__(self):
        self.face_detector = None
        self.eye_detector = None
        
        # Initialize face detection based on available libraries
        if DLIB_AVAILABLE:
            self.face_detector = dlib.get_frontal_face_detector()
            # Try to load the shape predictor for facial landmarks
            predictor_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'shape_predictor_68_face_landmarks.dat')
            if os.path.exists(predictor_path):
                self.shape_predictor = dlib.shape_predictor(predictor_path)
            else:
                self.shape_predictor = None
        elif MTCNN_AVAILABLE:
            self.face_detector = MTCNN()
        else:
            # Fall back to OpenCV's built-in face detector
            haar_cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
            if os.path.exists(haar_cascade_path):
                self.face_detector = cv2.CascadeClassifier(haar_cascade_path)
            
            # Eye detector
            eye_cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_eye.xml')
            if os.path.exists(eye_cascade_path):
                self.eye_detector = cv2.CascadeClassifier(eye_cascade_path)
    
    def base64_to_frame(self, base64_string):
        """Convert base64 image to OpenCV frame"""
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
            
        # Decode base64 string to image
        img_data = base64.b64decode(base64_string)
        img = Image.open(io.BytesIO(img_data))
        
        # Convert PIL Image to OpenCV format
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return cv_img
    
    def analyze_frame(self, frame):
        """Analyze a single video frame"""
        if frame is None or frame.size == 0:
            return None
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Initialize results
        results = {
            'face_detected': False,
            'eye_contact': 0,
            'facial_expression': 'neutral',
            'expression_score': 0,
            'head_position': 'centered'
        }
        
        # Detect faces based on available library
        faces = []
        
        if DLIB_AVAILABLE and self.face_detector:
            # Use dlib for face detection
            dlib_faces = self.face_detector(gray)
            if dlib_faces:
                results['face_detected'] = True
                for face in dlib_faces:
                    x, y, w, h = face.left(), face.top(), face.width(), face.height()
                    faces.append((x, y, w, h))
                    
                    # Check for facial landmarks if shape predictor is available
                    if self.shape_predictor:
                        shape = self.shape_predictor(gray, face)
                        # Analyze facial expression using landmarks
                        results['expression_score'] = self._analyze_expression_dlib(shape)
                        results['facial_expression'] = self._get_expression_label(results['expression_score'])
        
        elif MTCNN_AVAILABLE and self.face_detector:
            # Use MTCNN for face detection
            mtcnn_faces = self.face_detector.detect_faces(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if mtcnn_faces:
                results['face_detected'] = True
                for face in mtcnn_faces:
                    x, y, w, h = face['box']
                    faces.append((x, y, w, h))
                    
                    # Use keypoints for eye contact estimation
                    keypoints = face['keypoints']
                    left_eye = keypoints['left_eye']
                    right_eye = keypoints['right_eye']
                    results['eye_contact'] = self._estimate_eye_contact(frame, left_eye, right_eye)
                    
                    # Get confidence score for facial expression
                    results['expression_score'] = face['confidence']
                    results['facial_expression'] = self._get_expression_label(face['confidence'])
        
        elif self.face_detector:  # OpenCV Haar cascades
            # Detect faces
            faces_cv = self.face_detector.detectMultiScale(gray, 1.3, 5)
            if len(faces_cv) > 0:
                results['face_detected'] = True
                faces = faces_cv
                
                # Detect eyes for eye contact estimation
                if self.eye_detector:
                    for (x, y, w, h) in faces_cv:
                        roi_gray = gray[y:y+h, x:x+w]
                        eyes = self.eye_detector.detectMultiScale(roi_gray)
                        if len(eyes) >= 2:  # At least two eyes detected
                            results['eye_contact'] = 80  # Good eye contact score
                        elif len(eyes) == 1:
                            results['eye_contact'] = 50  # Moderate eye contact
                        else:
                            results['eye_contact'] = 20  # Poor eye contact
        
        # If we have face coordinates, analyze head position
        if faces:
            frame_height, frame_width = frame.shape[:2]
            x, y, w, h = faces[0]  # Take the first face
            
            # Calculate face center
            face_center_x = x + w/2
            face_center_y = y + h/2
            
            # Calculate deviation from frame center
            frame_center_x = frame_width / 2
            frame_center_y = frame_height / 2
            
            x_deviation = abs(face_center_x - frame_center_x) / frame_width
            y_deviation = abs(face_center_y - frame_center_y) / frame_height
            
            if x_deviation < 0.1 and y_deviation < 0.1:
                results['head_position'] = 'centered'
            elif x_deviation < 0.2 and y_deviation < 0.2:
                results['head_position'] = 'slightly off-center'
            else:
                results['head_position'] = 'off-center'
        
        return results
    
    def _estimate_eye_contact(self, frame, left_eye, right_eye):
        """Estimate eye contact based on eye positions"""
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate midpoint between eyes
        eye_center_x = (left_eye[0] + right_eye[0]) / 2
        eye_center_y = (left_eye[1] + right_eye[1]) / 2
        
        # Calculate deviation from frame center
        frame_center_x = frame_width / 2
        frame_center_y = frame_height / 2
        
        x_deviation = abs(eye_center_x - frame_center_x) / frame_width
        y_deviation = abs(eye_center_y - frame_center_y) / frame_height
        
        # Calculate eye contact score (0-100)
        eye_contact_score = 100 - (x_deviation + y_deviation) * 50
        return max(0, min(100, eye_contact_score))
    
    def _analyze_expression_dlib(self, shape):
        """Analyze facial expression using dlib landmarks"""
        # This is a simplified version - in a real implementation you'd use more sophisticated analysis
        # Here we just return a score based on mouth openness and eyebrow position
        
        # Get mouth points (48-68)
        mouth_points = np.array([[shape.part(i).x, shape.part(i).y] for i in range(48, 68)])
        
        # Calculate mouth aspect ratio
        mouth_width = np.linalg.norm(mouth_points[6] - mouth_points[0])
        mouth_height = np.linalg.norm(mouth_points[3] - mouth_points[9])
        mar = mouth_height / mouth_width
        
        # Get eyebrow points (17-27)
        left_eyebrow = np.array([[shape.part(i).x, shape.part(i).y] for i in range(17, 22)])
        right_eyebrow = np.array([[shape.part(i).x, shape.part(i).y] for i in range(22, 27)])
        
        # Calculate eyebrow position
        eyebrow_avg_height = (np.mean(left_eyebrow[:, 1]) + np.mean(right_eyebrow[:, 1])) / 2
        eye_avg_height = (shape.part(37).y + shape.part(38).y + shape.part(40).y + shape.part(41).y +
                         shape.part(43).y + shape.part(44).y + shape.part(46).y + shape.part(47).y) / 8
        
        # Higher eyebrows indicate surprise
        eyebrow_ratio = (eyebrow_avg_height - eye_avg_height) / eye_avg_height
        
        # Simple expression score
        if mar > 0.3 or eyebrow_ratio < -0.1:
            return 80  # Happy/surprised
        elif mar < 0.15 and eyebrow_ratio > 0.05:
            return 30  # Sad/angry
        else:
            return 50  # Neutral
    
    def _get_expression_label(self, score):
        """Convert expression score to label"""
        if score > 70:
            return 'happy'
        elif score > 60:
            return 'positive'
        elif score < 40:
            return 'negative'
        else:
            return 'neutral'
    
    def analyze_video(self, video_data):
        """Analyze a series of video frames"""
        if not video_data:
            return None
        
        # Analyze each frame
        frame_results = []
        for frame_base64 in video_data:
            frame = self.base64_to_frame(frame_base64)
            frame_result = self.analyze_frame(frame)
            if frame_result:
                frame_results.append(frame_result)
        
        if not frame_results:
            return None
        
        # Aggregate results across frames
        aggregated = {
            'face_detected_frames': sum(1 for r in frame_results if r['face_detected']),
            'total_frames': len(frame_results),
            'avg_eye_contact': np.mean([r['eye_contact'] for r in frame_results]),
            'avg_expression_score': np.mean([r['expression_score'] for r in frame_results]),
            'common_expression': self._get_most_common_expression(frame_results),
            'common_head_position': self._get_most_common_head_position(frame_results)
        }
        
        return aggregated
    
    def _get_most_common_expression(self, frame_results):
        """Get the most common facial expression"""
        expressions = [r['facial_expression'] for r in frame_results]
        if not expressions:
            return 'neutral'
        return max(set(expressions), key=expressions.count)
    
    def _get_most_common_head_position(self, frame_results):
        """Get the most common head position"""
        positions = [r['head_position'] for r in frame_results]
        if not positions:
            return 'centered'
        return max(set(positions), key=positions.count)