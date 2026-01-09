import speech_recognition as sr
import ollama
import subprocess
import os


os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
# To ukryje błędy ALSA w terminalu
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


def speak(text):
    # Używamy pełnej ścieżki do modułu zainstalowanego w venv
    piper_cmd = ['python3', '-m', 'piper', '--model', 'pl_PL-gosia-medium.onnx', '--output-raw']
    aplay_cmd = ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-']

    # Reszta kodu pozostaje bez zmian
    p1 = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(aplay_cmd, stdin=p1.stdout)

    p1.stdin.write(text.encode('utf-8'))
    p1.stdin.close()
    p2.wait()


def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        # Dodajemy dynamiczne dostosowanie do hałasu tła
        r.adjust_for_ambient_noise(source, duration=1)
        print("Słucham...")
        try:
            # timeout: ile sekund Jarvis czeka na początek mowy
            # phrase_time_limit: jak długa może być jedna wypowiedź
            audio = r.listen(source, timeout=5, phrase_time_limit=10)

            # Używamy modelu 'tiny' dla szybkości, by uniknąć "zapętlenia" procesora
            # Zmień z r.recognize_whisper(audio, language="polish") na:
            text = r.recognize_whisper(audio, language="polish", model="tiny")
            return text
        except (sr.WaitTimeoutError, Exception) as e:
            # Jeśli nikt nic nie mówi, po prostu wróć do pętli
            return ""


print("Jarvis gotowy...")
speak("Witaj. W czym mogę Ci dzisiaj pomóc?")

while True:
    input_text = listen()
    if input_text:
        print(f"Ty: {input_text}")

        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': 'Jesteś Jarvisem. Odpowiadaj bardzo krótko i po polsku.'},
            {'role': 'user', 'content': input_text}
        ])

        reply = response['message']['content']
        print(f"Jarvis: {reply}")
        speak(reply)