# -*- coding: utf-8 -*-
"""TTS_models

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1-kOI6Qbu5ULfT9_Y3FxedLCchF_03E6Z

# Установка и импорт библиотек
"""

!pip install vosk soundfile gtts transformers pydub > /dev/null 2>&1

!sudo apt-get install ffmpeg > /dev/null 2>&1

import os
import subprocess
import json
import requests
import soundfile as sf
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from IPython.display import Audio, display
from transformers import AutoModelForCausalLM, AutoTokenizer

"""# Класс VoiceAssistant

В этом классе реализованы функции:
* загрузка модели LLM - ai-forever/rugpt3small_based_on_gpt2
* загрузка модели Vosk для распознования голосовой команды и преобразования в текст
* загрузка аудиофайла-команды в формате mp3
* конвертация аудиофайла в формат wav
* использование Vosk для преобразования голосовой команды в текст
* генерация ответа на базе модели от ai-forever
* преобразование ответа в речь с помощью GoogleTTS (gTTS)
* вывод и автоматическое воспроизведение ответа
"""

class VoiceAssistant:
    def __init__(self, model_path, commands, llm_name, tts_lang="ru"):
        """
        Инициализация голосового помощника.
        Args:
            model_path (str): Путь к модели Vosk.
            commands (list): Список предопределённых команд.
            llm_name (str): Название модели LLM.
            tts_lang (str): Язык для TTS (по умолчанию "ru").
        """
        self.model_path = model_path
        self.commands = commands
        self.llm_name = llm_name
        self.tts_lang = tts_lang
        self.tokenizer = None
        self.model = None
        self._load_models()

    def _load_models(self):
        """Загрузка моделей Vosk и LLM."""
        # Загрузка модели Vosk
        if not os.path.exists(self.model_path):
            print("Скачивание модели Vosk...")
            subprocess.run(["wget", "-q", "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"])
            subprocess.run(["unzip", "-q", "vosk-model-small-ru-0.22.zip"])
            print("Модель Vosk успешно скачана.")
        else:
            print("Модель Vosk уже существует.")

        # Загрузка модели LLM
        print("Загрузка модели LLM...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.llm_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.llm_name)
        print("Модель LLM успешно загружена.")

    def download_audio(self, url, output_file):
        """
        Скачивание аудиофайла.
        Args:
            url (str): Ссылка на аудиофайл.
            output_file (str): Имя для сохранения аудиофайла.
        """
        if not os.path.exists(output_file):
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"Файл успешно скачан: {output_file}")
            else:
                print(f"Ошибка при скачивании файла: {url}")
        else:
            print(f"Аудиофайл {output_file} уже существует.")

    def convert_mp3_to_wav(self, input_file, output_file):
        """
        Конвертация MP3 в WAV с частотой 16 кГц и моно.
        Args:
            input_file (str): Путь к MP3-файлу.
            output_file (str): Путь к WAV-файлу.
        """
        command = f"ffmpeg -y -i {input_file} -ar 16000 -ac 1 {output_file}"
        subprocess.run(command, shell=True)
        if os.path.exists(output_file):
            print(f"Файл успешно конвертирован: {output_file}")
        else:
            print("Ошибка при конвертации файла.")

    def recognize_text(self, wav_file):
        """
        Распознавание текста из WAV-файла.
        Args:
            wav_file (str): Путь к WAV-файлу.
        Returns:
            str: Найденная команда или None.
        """
        model = Model(self.model_path)
        recognizer = KaldiRecognizer(model, 16000)
        with sf.SoundFile(wav_file) as audio:
            while True:
                data = audio.read(4000, dtype="int16").tobytes()
                if len(data) == 0:
                    break
                recognizer.AcceptWaveform(data)

        result = recognizer.FinalResult()
        recognized_text = json.loads(result)["text"]

        for command in self.commands:
            if command in recognized_text:
                return command
        return None

    def generate_response(self, command):
        """
        Генерация текста ответа на основе команды.
        Args:
            command (str): Команда.
        Returns:
            str: Сгенерированный ответ.
        """
        prompt = f"Ответь на следующую команду: '{command}'"
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(inputs.input_ids, max_new_tokens=50, do_sample=True, temperature=0.7)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

    def text_to_speech(self, text):
        """
        Преобразование текста в речь.
        Args:
            text (str): Текст для озвучивания.
        """
        tts = gTTS(text, lang=self.tts_lang)
        tts.save("response.mp3")
        display(Audio("response.mp3", autoplay=True))

    def process_audio(self, input_file):
        """
        Обработка аудиофайла: конвертация, распознавание, генерация ответа и озвучивание.
        Args:
            input_file (str): Путь к входному MP3-файлу.
        """
        wav_file = input_file.replace(".mp3", ".wav")
        self.convert_mp3_to_wav(input_file, wav_file)
        recognized_command = self.recognize_text(wav_file)

        if recognized_command:
            print(f"Распознана команда: {recognized_command}")
            response = self.generate_response(recognized_command)
            print(f"Ответ: {response}")
            self.text_to_speech(response)
        else:
            print("Команда не распознана.")

"""# Конфигурация

Необходимые файлы и константы вынесены отдельно для быстрой замены
"""

# Конфигурация
VOSK_MODEL_PATH = "vosk-model-small-ru-0.22"
AUDIO_URL = "https://storage.yandexcloud.net/datasetsforme/voice_comand/Voice_command_1.mp3"
INPUT_FILE = "Voice_command_1.mp3"
LLM_NAME = "ai-forever/rugpt3small_based_on_gpt2"
COMMANDS = [
    "расскажи анекдот",
    "объясни как включить свет",
    "ответь сколько будет два плюс два",
    "скажи интересный факт",
    "зачем нужны деревья",
    "расскажи про кошек",
    "объясни что такое воздух",
    "расскажи про планеты",
    "объясни что такое солнце",
    "скажи как узнать дату"
]

"""# Инференс

## 1. Создание голосового помошника
"""

# Создание экземпляра голосового помощника
assistant = VoiceAssistant(VOSK_MODEL_PATH, COMMANDS, LLM_NAME)

"""## 2. Скачивание аудиофайла по ссылке из конфигурации"""

# Скачивание аудиофайла
assistant.download_audio(AUDIO_URL, INPUT_FILE)

"""## 3. Вывод ответа на команду и автоматическое воспроизведение речи"""

# Обработка аудиофайла
assistant.process_audio(INPUT_FILE)