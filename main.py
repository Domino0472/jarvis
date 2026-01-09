import speech_recognition as sr
import ollama
import subprocess
import os
import sys  # Dodano sys do poprawnego wskazywania pythona

# Ukrywanie logów tensorflow i pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


def speak(text):
    # POPRAWKA 1: Używamy sys.executable, aby korzystać z python z venv, a nie systemowego
    piper_cmd = [sys.executable, '-m', 'piper', '--model', 'pl_PL-gosia-medium.onnx', '--output-raw']
    aplay_cmd = ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-']

    try:
        p1 = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(aplay_cmd, stdin=p1.stdout)

        p1.stdin.write(text.encode('utf-8'))
        p1.stdin.close()
        p2.wait()
    except Exception as e:
        print(f"Błąd TTS: {e}")


# Zmieniamy logikę: przekazujemy już otwarty mikrofon i obiekt recognizera
def listen(recognizer, source):
    try:
        # adjust_for_ambient_noise robimy RAZ w głównej pętli, nie tutaj
        print("Słucham...")

        # timeout=5 oznacza, że czeka 5 sekund na ciszę zanim uzna, że nikt nie mówi
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

        text = recognizer.recognize_whisper(audio, language="polish", model="tiny")
        return text
    except sr.WaitTimeoutError:
        return ""
    except Exception as e:
        print(f"Błąd rozpoznawania: {e}")
        return ""


# --- GŁÓWNY PROGRAM ---

print("Inicjalizacja Jarvis...")
r = sr.Recognizer()

# POPRAWKA 2: Otwieramy mikrofon TYLKO RAZ przed pętlą
# To sprawi, że błędy ALSA pojawią się tylko raz na starcie, a nie co chwilę
with sr.Microphone() as source:
    print("Kalibracja szumów (proszę o ciszę)...")
    r.adjust_for_ambient_noise(source, duration=2)
    print("Jarvis gotowy...")
    speak("Witaj. W czym mogę Ci dzisiaj pomóc?")

    while True:
        # Przekazujemy r i source do funkcji listen
        input_text = listen(r, source)

        if input_text:
            print(f"Ty: {input_text}")

            # Szybka weryfikacja czy tekst nie jest pusty
            if not input_text.strip():
                continue

            try:
                response = ollama.chat(model='llama3', messages=[
                    {'role': 'system', 'content': 'Jesteś Jarvisem. Odpowiadaj bardzo krótko i po polsku.'},
                    {'role': 'user', 'content': input_text}
                ])

                reply = response['message']['content']
                print(f"Jarvis: {reply}")
                speak(reply)
            except Exception as e:
                print(f"Błąd Ollama: {e}")