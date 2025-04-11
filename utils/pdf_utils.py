# utils/pdf_utils.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bson import ObjectId
import gridfs
import time
import base64

def generate_pdf_from_dashboard(dashboard_url, session_cookie):
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("http://localhost:5000")

    driver.add_cookie({
        'name': 'session',
        'value': session_cookie,
        'domain': 'localhost',
        'path': '/'
    })

    driver.get(dashboard_url)
    time.sleep(5)

    result = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True})
    pdf_base64 = result['data']
    pdf_bytes = base64.b64decode(pdf_base64)

    driver.quit()
    return pdf_bytes

def save_pdf_to_mongodb(db, pdf_bytes, email, filename):
    fs = gridfs.GridFS(db)
    pdf_id = fs.put(pdf_bytes, filename=filename, metadata={"email": email})
    return str(pdf_id)

def get_user_pdfs(db, email):
    fs = gridfs.GridFS(db)
    return list(fs.find({'metadata.email': email}))

def get_pdf_by_id(db, file_id):
    fs = gridfs.GridFS(db)
    return fs.get(ObjectId(file_id))

def delete_pdf_by_id(db, file_id):
    fs = gridfs.GridFS(db)
    fs.delete(ObjectId(file_id))
