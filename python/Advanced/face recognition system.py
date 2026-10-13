import face_recognition
import cv2
import numpy as np
import os
import pickle
from datetime import datetime

class FaceRecognizer:
    def __init__(self, dataset_path="faces", encoding_file="encodings.pkl"):
        self.dataset_path = dataset_path
        self.encoding_file = encoding_file
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_encodings()
    
    def load_encodings(self):
        if os.path.exists(self.encoding_file):
            with open(self.encoding_file, 'rb') as f:
                data = pickle.load(f)
                self.known_face_encodings = data['encodings']
                self.known_face_names = data['names']
            print(f"Loaded {len(self.known_face_names)} known faces")
    
    def save_encodings(self):
        with open(self.encoding_file, 'wb') as f:
            pickle.dump({'encodings': self.known_face_encodings, 'names': self.known_face_names}, f)
        print(f"Saved {len(self.known_face_names)} face encodings")
    
    def encode_faces_from_dataset(self):
        if not os.path.exists(self.dataset_path):
            os.makedirs(self.dataset_path)
            print(f"Created {self.dataset_path}. Add face images there.")
            return
        
        for person_name in os.listdir(self.dataset_path):
            person_path = os.path.join(self.dataset_path, person_name)
            if not os.path.isdir(person_path):
                continue
            
            for image_file in os.listdir(person_path):
                if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(person_path, image_file)
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_names.append(person_name)
                        print(f"Encoded {person_name} from {image_file}")
        
        self.save_encodings()
    
    def add_face(self, name, image_path):
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        
        if encodings:
            self.known_face_encodings.append(encodings[0])
            self.known_face_names.append(name)
            self.save_encodings()
            print(f"Added face for {name}")
            
            # Also save image to dataset
            person_dir = os.path.join(self.dataset_path, name)
            os.makedirs(person_dir, exist_ok=True)
            img = cv2.imread(image_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(os.path.join(person_dir, f"{timestamp}.jpg"), img)
            return True
        else:
            print("No face found in image")
            return False
    
    def recognize_faces(self, image, tolerance=0.6):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance)
            name = "Unknown"
            
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
            
            face_names.append(name)
        
        return face_locations, face_names
    
    def draw_results(self, image, face_locations, face_names):
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(image, (left, top), (right, bottom), color, 2)
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(image, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
        return image
    
    def recognize_from_image(self, image_path):
        image = cv2.imread(image_path)
        face_locations, face_names = self.recognize_faces(image)
        result = self.draw_results(image, face_locations, face_names)
        
        cv2.imshow("Face Recognition", result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return list(zip(face_names, face_locations))
    
    def recognize_from_webcam(self):
        video_capture = cv2.VideoCapture(0)
        
        print("Press 'q' to quit, 's' to save unknown face")
        
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            # Resize for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            face_locations, face_names = self.recognize_faces(small_frame)
            
            # Scale back up
            face_locations = [(top*2, right*2, bottom*2, left*2) for (top, right, bottom, left) in face_locations]
            
            result = self.draw_results(frame, face_locations, face_names)
            cv2.imshow('Face Recognition', result)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s') and face_locations:
                # Save unknown face
                name = input("Enter name for this face: ").strip()
                if name:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    person_dir = os.path.join(self.dataset_path, name)
                    os.makedirs(person_dir, exist_ok=True)
                    top, right, bottom, left = face_locations[0]
                    face_crop = frame[top:bottom, left:right]
                    cv2.imwrite(os.path.join(person_dir, f"{timestamp}.jpg"), face_crop)
                    print(f"Saved face for {name}")
                    # Re-encode all faces
                    self.encode_faces_from_dataset()
        
        video_capture.release()
        cv2.destroyAllWindows()
    
    def run(self):
        print("=== Face Recognition System ===")
        
        while True:
            print("\n1. Encode faces from dataset")
            print("2. Add new face")
            print("3. Recognize from image")
            print("4. Recognize from webcam")
            print("5. Exit")
            
            choice = input("\nChoose: ").strip()
            
            if choice == '1':
                self.encode_faces_from_dataset()
            
            elif choice == '2':
                name = input("Person name: ").strip()
                image_path = input("Image path: ").strip()
                self.add_face(name, image_path)
            
            elif choice == '3':
                image_path = input("Image path: ").strip()
                self.recognize_from_image(image_path)
            
            elif choice == '4':
                self.recognize_from_webcam()
            
            elif choice == '5':
                print("Goodbye!")
                break

if __name__ == "__main__":
    recognizer = FaceRecognizer()
    recognizer.run()
