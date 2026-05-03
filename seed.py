import json
import os
from pymongo import MongoClient

# Connect to your local MongoDB container
# (If you set a username/password, update this URI)
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["security_practice"]
exams_collection = db["exams"]

def seed_database(root_dir):
    # Clear existing data to avoid duplicates during testing
    exams_collection.delete_many({})
    
    for root, dirs, files in os.walk(root_dir):
        if "exam_data.json" in files:
            file_path = os.path.join(root, "exam_data.json")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Extract routing metadata from the directory structure
                # Example path: .../quiz_screenshots/Practice_set_1/exam_1/exam_data.json
                parts = file_path.split(os.sep)
                practice_set = parts[-3]
                exam_number = parts[-2]
                
                # Create a clean document
                exam_document = {
                    "practice_set": practice_set,
                    "exam_id": exam_number,
                    "course": data.get("course", practice_set),
                    "questions": data.get("questions", [])
                }
                
                # Insert into MongoDB
                exams_collection.insert_one(exam_document)
                print(f"Inserted: {practice_set} - {exam_number} with {len(exam_document['questions'])} questions.")

if __name__ == "__main__":
    # Point this to your target directory
    target_directory = "quiz_screenshots"
    if os.path.exists(target_directory):
        seed_database(target_directory)
        print("Database seeding complete.")
    else:
        print(f"Directory {target_directory} not found.")