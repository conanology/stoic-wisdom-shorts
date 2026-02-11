
import importlib

def check_import(module_name, class_name):
    try:
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        print(f"✅ Found {class_name} in {module_name}")
        return True
    except ImportError:
        print(f"❌ Module {module_name} not found")
    except AttributeError:
        print(f"❌ Class {class_name} NOT in {module_name}")
    return False

# Attempt known locations
candidates = [
    ("moviepy.video.io.VideoFileClip", "VideoFileClip"),
    ("moviepy.audio.io.AudioFileClip", "AudioFileClip"),
    ("moviepy.video.compositing.CompositeVideoClip", "CompositeVideoClip"),
    ("moviepy.audio.AudioClip", "CompositeAudioClip"), # v2.0 structure often puts it here
    ("moviepy.audio.compositing.CompositeAudioClip", "CompositeAudioClip"),
    ("moviepy.video.VideoClip", "VideoClip"),
    ("moviepy.video.VideoClip", "ColorClip"), # often in VideoClip or nearby
    ("moviepy.video.VideoClip", "TextClip"),
    ("moviepy.video.fx", "FadeIn"), # effects
]

for mod, cls in candidates:
    check_import(mod, cls)
