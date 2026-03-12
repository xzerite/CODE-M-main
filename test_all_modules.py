#!/usr/bin/env python3
"""
تشغيل كل الموديولات بالتتابع لمعرفة أيها يعمل وأيها يعطي أخطاء
Run all modules one by one to see which work and which have errors
"""
import subprocess
import sys
import os

# الملفات التي نختبرها (بدون هذا الملف والقائمة الرئيسية)
MODULES = [
    "voice_note_recorder.py",
    "voice_note_player.py",
    "color_detection.py",
    "age_gender_detection.py",
    "traffic_sign_detection.py",
    "currency_recognition.py",
    "text_recognition_ocr.py",
    "object_distance_calculator.py",
    "face_recognition.py",
    "register_new_face.py",
    "image_caption_generator.py",
    "voice_object_search.py",
]

# وقت أقصى لكل سكربت (ثواني) - لو ما انتهى نعتبره "بدأ بدون خطأ"
TIMEOUT = 8

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 60)
    print("اختبار تشغيل الموديولات | Testing all modules")
    print("=" * 60)

    results = []
    for name in MODULES:
        if not os.path.isfile(name):
            results.append((name, "SKIP", "الملف غير موجود"))
            continue
        try:
            r = subprocess.run(
                [sys.executable, name],
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                cwd=script_dir,
            )
            if r.returncode == 0:
                results.append((name, "OK", ""))
            else:
                err = (r.stderr or r.stdout or "").strip()
                # أخذ آخر سطرين من الخطأ عادةً كافية
                err_lines = err.split("\n")
                short_err = "\n".join(err_lines[-4:]) if len(err_lines) > 4 else err
                results.append((name, "FAIL", short_err))
        except subprocess.TimeoutExpired:
            # انتهى الوقت = السكربت بدأ ولم يخرج بخطأ سريع
            results.append((name, "OK (timeout)", "تشغّل ثم انتهت المهلة"))
        except Exception as e:
            results.append((name, "FAIL", str(e)))

    # طباعة النتائج
    print()
    for name, status, msg in results:
        if status.startswith("OK"):
            print(f"  [OK]  {name}")
        elif status == "SKIP":
            print(f"  [--]  {name}  ({msg})")
        else:
            print(f"  [X]   {name}")
            if msg:
                for line in msg.split("\n"):
                    print(f"        {line}")
    print()
    print("=" * 60)
    ok = sum(1 for _, s, _ in results if s.startswith("OK"))
    fail = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"النتيجة: {ok} يعمل | {fail} فيه خطأ")
    print("=" * 60)

if __name__ == "__main__":
    main()
