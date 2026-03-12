# دليل التثبيت | Installation Guide

## المشكلة | The Problem

عند تشغيل `pip install -r requirements.txt` قد يفشل التثبيت بسبب:

- **PyAudio**: يحتاج مكتبة PortAudio على النظام (`portaudio.h` not found).
- **face_recognition**: يعتمد على **dlib** الذي يحتاج **CMake** للبناء.

When you run `pip install -r requirements.txt`, installation may fail because:

- **PyAudio** requires the PortAudio system library (`portaudio.h` not found).
- **face_recognition** depends on **dlib**, which requires **CMake** to build.

---

## الحل على macOS (باستخدام Homebrew) | Solution on macOS (using Homebrew)

### 1. تثبيت Homebrew (إن لم يكن مثبتاً)

إذا لم يكن Homebrew مثبتاً:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. تثبيت التبعيات النظامية | Install system dependencies

```bash
brew install portaudio   # مطلوب لـ PyAudio
brew install cmake      # مطلوب لـ dlib (face_recognition)
brew install tesseract  # اختياري - للتعرف على النص (OCR)
```

### 3. تثبيت مكتبات بايثون | Install Python packages

```bash
pip install -r requirements.txt
```

---

## إذا استمرت مشكلة PyAudio | If PyAudio still fails

جرّب تثبيت PyAudio مع تحديد مسار PortAudio:

Try installing PyAudio with the PortAudio path:

```bash
# تأكد أن portaudio مثبت
brew install portaudio

# ثم ثبّت PyAudio (مع المسار لـ Apple Silicon إن لزم)
pip install --global-option="build_ext" --global-option="-I/opt/homebrew/include" --global-option="-L/opt/homebrew/lib" PyAudio
```

أو استخدم wheel جاهز إن وُجد لإصدارك من Python و macOS.

Or use a pre-built wheel if available for your Python and macOS version.

---

## الحل على Windows | Solution on Windows

### 1. تثبيت CMake (مطلوب لـ face_recognition / dlib)

**الطريقة أ – من الموقع (مفضّل):**

- حمّل المثبّت من: https://cmake.org/download/
- اختر **Windows x64 Installer**
- أثناء التثبيت اختر **"Add CMake to the system PATH"**

**الطريقة ب – من سطر الأوامر:**

```cmd
winget install Kitware.CMake
```

أو مع Chocolatey:

```cmd
choco install cmake
```

### 2. تثبيت Visual Studio Build Tools (مطلوب لبناء dlib)

- حمّل **Build Tools for Visual Studio** من: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- عند التثبيت فعّل **"Desktop development with C++"**.

### 3. تثبيت PyAudio

جرّب أولاً:

```cmd
pip install PyAudio
```

إذا فشل، استخدم **pipwin**:

```cmd
pip install pipwin
pipwin install pyaudio
```

أو حمّل ملف **wheel** المناسب لإصدار بايثون ونظامك من:  
https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio  
ثم:

```cmd
pip install اسم_الملف.whl
```

### 4. تثبيت Tesseract (اختياري – للتعرف على النص OCR)

- حمّل من: https://github.com/UB-Mannheim/tesseract/wiki
- ثبّت وضَع مسار المجلد `tesseract.exe` في **PATH** (أو حدّد المسار في الكود كما في `text_recognition_ocr.py`).

### 5. تثبيت مكتبات بايثون

```cmd
pip install -r requirements.txt
```

---

## ملخص الأوامر | Command summary

**macOS:**

```bash
brew install portaudio cmake tesseract
pip install -r requirements.txt
```

**Windows:**

1. تثبيت CMake وإضافته إلى PATH.
2. تثبيت Visual Studio Build Tools (C++).
3. `pip install PyAudio` أو استخدام pipwin/wheel إذا فشل.
4. تثبيت Tesseract (اختياري) وإضافته إلى PATH.
5. `pip install -r requirements.txt`

بعد تنفيذ هذه الخطوات يجب أن يكتمل التثبيت بنجاح.

After following these steps, installation should complete successfully.
