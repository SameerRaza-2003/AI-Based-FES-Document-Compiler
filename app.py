from flask import Flask, render_template, request, jsonify
from PIL import Image
import pytesseract
from fpdf import FPDF
import os
import uuid
import google.generativeai as genai
import fitz  # PyMuPDF

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Classification priority
DOCUMENT_PRIORITY = {
    "University Degree": 1,
    "University Transcript": 2,
    "HSSC Certificate": 3,
    "HSSC Detailed Marksheet": 4,
    "O Levels": 5,
    "Matric Certificate": 5,
    "SSC Certificate": 5,
    "Matric Detailed Marksheet": 6,
    "SSC Detailed Marksheet": 6,
    "Unknown": 999
}


def classify_with_gemini(text):
    prompt = f"""
You are a document classifier. Based on the extracted OCR text below, classify the document into one of the following categories:
- University Degree
- University Transcript
- HSSC Certificate
- HSSC Detailed Marksheet
- O Levels
- SSC Certificate
- SSC Detailed Marksheet
- CNIC
- Passport
- IELTS

Return only the most appropriate category name without explanation.

Text:
{text}
    """.strip()

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    label = response.text.strip()
    print("Gemini classified as:", label)
    return label


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/upload', methods=["POST"])
def upload():
    files = request.files.getlist("images[]")
    result = []

    for file in files:
        if not file:
            continue

        ext = file.filename.rsplit('.', 1)[-1].lower()
        is_pdf = ext == "pdf"

        if is_pdf:
            # Save PDF temporarily
            pdf_id = str(uuid.uuid4())
            pdf_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")
            file.save(pdf_path)

            try:
                doc = fitz.open(pdf_path)
                for i, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=200)
                    img_id = f"{pdf_id}_p{i}"
                    img_path = os.path.join(UPLOAD_FOLDER, f"{img_id}.jpg")
                    pix.save(img_path)

                    # OCR & Classification
                    image = Image.open(img_path).convert("RGB")
                    gray = image.convert("L").resize((image.width * 2, image.height * 2))
                    binarized = gray.point(lambda x: 0 if x < 150 else 255, '1')
                    text = pytesseract.image_to_string(binarized, lang="eng")

                    try:
                        doc_type = classify_with_gemini(text)
                        if not doc_type:
                            raise ValueError("Empty classification")
                    except Exception as e:
                        print("Gemini failed:", e)
                        doc_type = "Unknown"

                    result.append({
                        "id": img_id,
                        "filename": f"{img_id}.jpg",
                        "doc_type": doc_type
                    })
                doc.close()
            except Exception as e:
                print("PDF conversion failed:", e)
            finally:
                try:
                    os.remove(pdf_path)
                except Exception as e:
                    print(f"PDF remove error: {e}")
        else:
            # Handle image upload
            img_id = str(uuid.uuid4())
            path = os.path.join(UPLOAD_FOLDER, img_id + ".jpg")
            image = Image.open(file).convert("RGB")
            image.save(path)

            gray = image.convert("L").resize((image.width * 2, image.height * 2))
            binarized = gray.point(lambda x: 0 if x < 150 else 255, '1')
            text = pytesseract.image_to_string(binarized, lang="eng")

            try:
                doc_type = classify_with_gemini(text)
                if not doc_type:
                    raise ValueError("Empty classification")
            except Exception as e:
                print("Gemini failed:", e)
                doc_type = "Unknown"

            result.append({
                "id": img_id,
                "filename": img_id + ".jpg",
                "doc_type": doc_type
            })

    # Sort by priority
    result.sort(key=lambda x: DOCUMENT_PRIORITY.get(x["doc_type"], 999))
    return jsonify(result)



@app.route('/generate_pdf', methods=["POST"])
def generate_pdf():
    data = request.json
    ordered = data["ordered"]
    rotations = data.get("rotations", {})  

    pdf = FPDF()

    for fname in ordered:
        path = os.path.join(UPLOAD_FOLDER, fname)
        img = Image.open(path)

        # Apply rotation if needed
        angle = int(rotations.get(fname, 0))
        if angle:
            img = img.rotate(-angle, expand=True)  

        # Save rotated version temporarily
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{fname}")
        img.convert("RGB").save(temp_path)

        pdf.add_page()
        pdf.image(temp_path, x=10, y=10, w=190)

        # Delete temp image
        os.remove(temp_path)

    output_path = os.path.join(UPLOAD_FOLDER, "compiled.pdf")
    pdf.output(output_path)

    return jsonify({"url": "/static/uploads/compiled.pdf"})


@app.route('/delete_image/<filename>', methods=["POST"])
def delete_image(filename):
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, filename))
    except Exception as e:
        print(f"Error deleting {filename}: {e}")
    return '', 204


@app.route('/crop_image', methods=["POST"])
def crop_image():
    file = request.files["image"]
    filename = request.form["filename"]
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    image = Image.open(file).convert("RGB")
    image.save(save_path)
    return '', 204


if __name__ == '__main__':
    app.run(debug=True)
