from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import torch

DetectorFactory.seed = 0

MODEL_NAME = "Helsinki-NLP/opus-mt-sv-en"

print("Loading local translation model...")
tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
model = MarianMTModel.from_pretrained(MODEL_NAME)

def translate_to_english(text: str) -> str:
    if not text or not text.strip():
        return text

    try:
        paragraphs = text.split("\n")
        translated_paragraphs = []
        
        for para in paragraphs:
            if not para.strip():
                translated_paragraphs.append("")
                continue
            
            encoded = tokenizer(para, 
                                return_tensors="pt", 
                                padding=True, 
                                truncation=True, 
                                max_length=512)

            with torch.no_grad():
                translated = model.generate(**encoded)

            translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
            translated_paragraphs.append(translated_text)
            
        return "\n".join(translated_paragraphs)
            
    except Exception:
        print("Failed to translate to English")

    return text


def detect_if_swedish(text: str) -> bool:
    if not text or not text.strip():
        return False

    try:
        lang = detect(text)
        if lang == 'sv':
            return True
        
    except LangDetectException:
        print("Failed to detect language")

    return False