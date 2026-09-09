import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import pygame
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import uuid
import os
import time
from fpdf import FPDF  # <- NEW IMPORT

# for Output translation 
LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'hi': 'Hindi',
    'ar': 'Arabic',
    'zh-cn': 'Chinese (Simplified)',
    'ja': 'Japanese',
    'ru': 'Russian',
    'it': 'Italian'
}

TTS_LANG_CODES = {
    'en': 'en',
    'es': 'es',
    'fr': 'fr',
    'de': 'de',
    'hi': 'hi',
    'ar': 'ar',
    'zh-cn': 'zh-cn',
    'ja': 'ja',
    'ru': 'ru',
    'it': 'it'
}

class VoiceTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Language Detection Voice Translator")
        self.root.geometry("620x650")
        self.root.configure(bg="#282c34")
        self.root.resizable(False, False)

        pygame.mixer.init()
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.listening = False
        self.last_translated_text = ""

        self.create_widgets()

    def create_widgets(self):
        label_style = {'font': ("Helvetica", 11, "bold"), 'bg': '#282c34', 'fg': 'white'}
        text_style = {'font': ("Helvetica", 11), 'bg': '#3c3f41', 'fg': 'white', 'insertbackground': 'white'}

        frame = tk.Frame(self.root, bg="#282c34", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        self.auto_detect_var = tk.BooleanVar(value=True)
        auto_chk = tk.Checkbutton(frame, text="Auto Detect Input Language", variable=self.auto_detect_var,
                                  bg="#282c34", fg="white", font=("Helvetica", 11, "bold"),
                                  activebackground="#282c34", activeforeground="white", selectcolor="#282c34")
        auto_chk.grid(row=0, column=0, sticky="w", pady=(0, 10))

        tk.Label(frame, text="Output Language (Translation):", **label_style).grid(row=1, column=0, sticky="w")
        self.output_lang_var = tk.StringVar(value='en')
        output_dropdown = ttk.Combobox(
            frame, textvariable=self.output_lang_var, values=list(LANGUAGES.keys()), state='readonly',
            font=("Helvetica", 11))
        output_dropdown.grid(row=2, column=0, sticky="ew", pady=5)
        output_dropdown.bind("<<ComboboxSelected>>", self.update_output_lang_label)
        self.output_lang_label = tk.Label(frame, text=f"({LANGUAGES['en']})", **label_style)
        self.output_lang_label.grid(row=2, column=1, sticky="w")

        tk.Label(frame, text="Recognized Text:", **label_style).grid(row=3, column=0, sticky="w", pady=(15, 0))
        self.recognized_text = tk.Text(frame, height=6, width=70, wrap="word", **text_style,
                                       state='disabled', relief="solid", borderwidth=1)
        self.recognized_text.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        recognized_scroll = ttk.Scrollbar(frame, command=self.recognized_text.yview)
        recognized_scroll.grid(row=4, column=2, sticky='ns', pady=(0, 10))
        self.recognized_text['yscrollcommand'] = recognized_scroll.set

        tk.Label(frame, text="Translated Text:", **label_style).grid(row=5, column=0, sticky="w", pady=(10, 0))
        self.translated_text = tk.Text(frame, height=6, width=70, wrap="word", **text_style,
                                       state='disabled', relief="solid", borderwidth=1)
        self.translated_text.grid(row=6, column=0, columnspan=2)
        translated_scroll = ttk.Scrollbar(frame, command=self.translated_text.yview)
        translated_scroll.grid(row=6, column=2, sticky='ns')
        self.translated_text['yscrollcommand'] = translated_scroll.set

        btn_frame = tk.Frame(frame, bg="#282c34")
        btn_frame.grid(row=7, column=0, columnspan=3, pady=20, sticky="ew")

        self.start_btn = tk.Button(btn_frame, text="Start Listening", command=self.start_listening,
                                   bg="#4caf50", fg="white", font=("Helvetica", 11, "bold"),
                                   relief="flat", padx=15, pady=8)
        self.start_btn.pack(side="left", padx=5, fill="x", expand=True)

        self.stop_btn = tk.Button(btn_frame, text="Stop Listening", command=self.stop_listening,
                                  bg="#f44336", fg="white", font=("Helvetica", 11, "bold"),
                                  relief="flat", padx=15, pady=8, state="disabled")
        self.stop_btn.pack(side="left", padx=5, fill="x", expand=True)

        self.save_btn = tk.Button(btn_frame, text="Save Translation as MP3", command=self.save_translation_mp3,
                                  bg="#2196f3", fg="white", font=("Helvetica", 11, "bold"),
                                  relief="flat", padx=15, pady=8)
        self.save_btn.pack(side="left", padx=5, fill="x", expand=True)

        # NEW BUTTON: Save as PDF
        self.save_pdf_btn = tk.Button(btn_frame, text="Save as PDF", command=self.save_translation_pdf,
                                      bg="#9c27b0", fg="white", font=("Helvetica", 11, "bold"),
                                      relief="flat", padx=15, pady=8)
        self.save_pdf_btn.pack(side="left", padx=5, fill="x", expand=True)

    def update_output_lang_label(self, event=None):
        lang_code = self.output_lang_var.get()
        lang_name = LANGUAGES.get(lang_code, "")
        self.output_lang_label.config(text=f"({lang_name})")

    def start_listening(self):
        if self.listening:
            return
        self.listening = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        threading.Thread(target=self.listen_and_translate_loop, daemon=True).start()

    def stop_listening(self):
        self.listening = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def listen_and_translate_loop(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)

                while self.listening:
                    audio = self.recognizer.listen(source, phrase_time_limit=5)

                    try:
                        recognized_text = self.recognizer.recognize_google(audio, language='en-US')

                        if self.auto_detect_var.get():
                            detected = self.translator.detect(recognized_text)
                            input_lang = detected.lang
                        else:
                            input_lang = 'en'

                        self.append_text(self.recognized_text, f"[{input_lang}] " + recognized_text)

                        output_lang = self.output_lang_var.get()
                        translated = self.translator.translate(recognized_text, src=input_lang, dest=output_lang)
                        self.append_text(self.translated_text, translated.text)

                        self.last_translated_text = translated.text
                        self.speak_text(translated.text, output_lang)

                    except sr.UnknownValueError:
                        self.append_text(self.recognized_text, "[Could not understand audio]")
                    except sr.RequestError as e:
                        self.append_text(self.recognized_text, f"[Speech service error: {e}]")
                    except Exception as e:
                        self.append_text(self.recognized_text, f"[Error: {e}]")

        except Exception as e:
            messagebox.showerror("Error", f"Microphone error:\n{e}")
            self.listening = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')

    def append_text(self, widget, text):
        widget.config(state='normal')
        widget.insert('end', text + "\n")
        widget.see('end')
        widget.config(state='disabled')

    def speak_text(self, text, lang_code):
        lang = TTS_LANG_CODES.get(lang_code, 'en')
        try:
            filename = f"temp_{uuid.uuid4().hex}.mp3"
            tts = gTTS(text=text, lang=lang)
            tts.save(filename)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            os.remove(filename)
        except Exception as e:
            self.append_text(self.recognized_text, f"[TTS Error: {e}]")

    def save_translation_mp3(self):
        if not self.last_translated_text.strip():
            messagebox.showwarning("Warning", "No translated text to save!")
            return

        filename = simpledialog.askstring("Save MP3", "Enter file name (without extension):")
        if not filename:
            return

        filename = filename.strip()
        if not filename:
            messagebox.showwarning("Warning", "Invalid file name!")
            return

        lang = TTS_LANG_CODES.get(self.output_lang_var.get(), 'en')
        try:
            tts = gTTS(text=self.last_translated_text, lang=lang)
            full_path = filename + ".mp3"
            tts.save(full_path)
            messagebox.showinfo("Success", f"File saved successfully:\n{full_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save MP3:\n{e}")

    # NEW FUNCTION
    def save_translation_pdf(self):
        if not self.last_translated_text.strip():
            messagebox.showwarning("Warning", "No translated text to save!")
            return

        filename = simpledialog.askstring("Save PDF", "Enter file name (without extension):")
        if not filename:
            return

        filename = filename.strip()
        if not filename:
            messagebox.showwarning("Warning", "Invalid file name!")
            return

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)

            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Voice Translator Output", ln=True, align='C')
            pdf.ln(10)

            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Recognized Text:", ln=True)
            pdf.set_font("Arial", size=12)
            original_text = self.recognized_text.get("1.0", "end").strip()
            pdf.multi_cell(0, 10, original_text)
            pdf.ln(5)

            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Translated Text:", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, self.last_translated_text)

            full_path = filename + ".pdf"
            pdf.output(full_path)
            messagebox.showinfo("Success", f"PDF saved successfully:\n{full_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceTranslatorApp(root)
    root.mainloop()