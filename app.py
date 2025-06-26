from flask import Flask, request, jsonify, send_file
from textblob import TextBlob
from flask_cors import CORS
from googletrans import Translator
from PIL import Image
import pytesseract
from io import BytesIO
from fpdf import FPDF
from datetime import datetime


app = Flask(__name__)
CORS(app)

translator = Translator()

#SENTIMENT ANALISIS NYA
@app.route('/api/sentiment', methods=['POST'])
def sentiment():
    data = request.get_json()
    catatan = data.get('catatan')
    try:
        deteksi_bahasa = translator.detect(catatan).lang
        if deteksi_bahasa in ['id', 'ms'] :
            catatan_en = translator.translate(catatan, dest='en')
            blob = TextBlob(catatan_en.text)
        else :
            blob = TextBlob(catatan)
        return jsonify({
        "polarity": blob.sentiment.polarity,
        "subjectivity": blob.sentiment.subjectivity
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        


# MASIH KURANG, CUMA BISA MNGECEK DARI KALIMAT YANG BERBAHSA INGGRIS AJA
@app.route('/api/typo', methods=['POST'])
def cek_typo():
    data = request.get_json()
    catatan = data.get('catatan')
    try:
        corrected_text = TextBlob(catatan).correct()
        return jsonify({"catatan_diperbaiki": str(corrected_text)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# ML CONVERT DARI FOTO KE TEXT, TESERACT ORC
@app.route('/api/convert', methods=['POST'])
def ocr_from_file():
    if 'image' not in request.files:
        return jsonify({'error': 'File gambar tidak ditemukan'}), 400
    file = request.files['image']
    try:
        image = Image.open(file.stream)
        text = pytesseract.image_to_string(image)
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#CONVERT TEXT TO PDF
@app.route('/api/pdf', methods=['POST'])
def text_to_pdf():
    data = request.get_json()
    title = data.get('title')
    text = data.get('text')
    garis = "==========================================================================="
    tanggal = f"Created at {datetime.now()}"
    if not text or not title:
        return jsonify({'error': 'Teks tidak ditemukan'}), 400

    try:
        pdf = FPDF()
        pdf.add_page()
        
        # JUDUL CATATAN
        pdf.set_font("Arial", size=28, style='B')
        for line in title.split('\n'):
            pdf.multi_cell(0, 10, txt=line)
        pdf.ln(2)
        
        #TANGGAL
        pdf.set_font("Arial", size=12)
        for line in tanggal.split('\n'):
            pdf.multi_cell(0, 10, txt=line)
        
        #GARIS PEMBATAS
        pdf.set_font("Arial", size=12)
        for line in garis.split('\n'):
            pdf.multi_cell(0, 10, txt=line)
       
        pdf.ln(5)
       
        # ISI TEXT UTAMA
        pdf.set_font("Arial", size=12)
        for line in text.split('\n'):
            pdf.multi_cell(0, 10, txt=line)

        pdf_output = BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        pdf_output.write(pdf_bytes)
        pdf_output.seek(0)

        return send_file(pdf_output, as_attachment=True, download_name="catatan.pdf", mimetype='application/pdf')

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/testing', methods=['GET'])
def testing():
    dataku = ['alif']
    return jsonify([dataku])    
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000 ,debug=True)