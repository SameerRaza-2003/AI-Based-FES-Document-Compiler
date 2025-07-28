from PIL import Image
import pytesseract
import google.generativeai as genai

# ========== Step 1: Configure Gemini ==========
genai.configure(api_key="")  # 🔁 Replace with your actual Gemini API key

model = genai.GenerativeModel("gemini-2.0-flash")

# ========== Step 2: Load Image and Extract Text ==========
image_path = "mara jee karesult].jpg"  # 🔁 Change to your image filename
img = Image.open(image_path)

# Extract text using Tesseract
extracted_text = pytesseract.image_to_string(img)
print("Extracted Text:\n", extracted_text)

# ========== Step 3: Ask Gemini for Classification ==========
prompt = f"""
This is the text extracted from a document:

\"\"\"{extracted_text}\"\"\"

Can you tell me what kind of document this is?
Classify it as one of the following:
Passport, Degree, Transcript, NIC, Visa,Matric, hssc result or Other. just one word answer
"""

response = model.generate_content(prompt)

# ========== Step 4: Show Gemini’s Response ==========
print("\n Gemini Classification:", response.text.strip())
