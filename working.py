
#
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image
import pytesseract
from fpdf import FPDF
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust if needed

# Keywords for classification
DOCUMENT_KEYWORDS = {
    "matric": ["ssc", "secondary school certificate", "matriculation"],
    "inter": ["hssc", "intermediate", "higher secondary"],
    "cnic": ["cnic", "national identity card"],
    "passport": ["passport"],
    "ielts": ["ielts", "english language testing"],
    "transcript": ["transcript", "grades", "marks sheet"]
}


def identify_doc_type(text):
    text = text.lower()
    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return doc_type
    return "unknown"


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/upload', methods=["POST"])
def upload():
    files = request.files.getlist("images[]")
    result = []
    for file in files:
        img_id = str(uuid.uuid4())
        path = os.path.join(UPLOAD_FOLDER, img_id + ".jpg")
        image = Image.open(file).convert("RGB")
        image.save(path)

        # OCR + classification
        gray = image.convert("L").resize((image.width * 2, image.height * 2))
        binarized = gray.point(lambda x: 0 if x < 150 else 255, '1')
        text = pytesseract.image_to_string(binarized)
        doc_type = identify_doc_type(text)

        result.append({
            "id": img_id,
            "filename": img_id + ".jpg",
            "doc_type": doc_type
        })

    return jsonify(result)


@app.route('/generate_pdf', methods=["POST"])
def generate_pdf():
    data = request.json
    pdf = FPDF()
    for fname in data["ordered"]:
        path = os.path.join(UPLOAD_FOLDER, fname)
        pdf.add_page()
        pdf.image(path, x=10, y=10, w=190)
    output_path = os.path.join(UPLOAD_FOLDER, "compiled.pdf")
    pdf.output(output_path)
    return jsonify({"url": "/static/uploads/compiled.pdf"})


if __name__ == '__main__':
    app.run(debug=True)


