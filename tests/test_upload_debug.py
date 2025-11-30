import requests
import os

def test_upload():
    url = "http://localhost:8000/api/upload"
    
    # Create dummy files
    with open("dummy_pyq.pdf", "wb") as f:
        f.write(b"dummy pdf content")
    with open("dummy_syllabus.pdf", "wb") as f:
        f.write(b"dummy syllabus content")
        
    try:
        files = [
            ('pyqs', ('dummy_pyq.pdf', open('dummy_pyq.pdf', 'rb'), 'application/pdf')),
            ('syllabus', ('dummy_syllabus.pdf', open('dummy_syllabus.pdf', 'rb'), 'application/pdf'))
        ]
        
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    finally:
        # Cleanup
        if os.path.exists("dummy_pyq.pdf"):
            os.remove("dummy_pyq.pdf")
        if os.path.exists("dummy_syllabus.pdf"):
            os.remove("dummy_syllabus.pdf")

if __name__ == "__main__":
    test_upload()
