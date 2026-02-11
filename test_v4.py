from core.quran_v4_api import get_verse_audio_with_timings, get_verse_words

def test():
    print("Testing V4 API...")
    reciter_id = 7 # Mishary
    surah = 112
    ayah = 1
    
    print(f"Fetching audio for {surah}:{ayah}...")
    url, segments = get_verse_audio_with_timings(reciter_id, surah, ayah)
    print(f"URL: {url}")
    print(f"Segments: {len(segments)}")
    if segments:
        print(f"First segment: {segments[0]}")
        
    print(f"\nFetching words for {surah}:{ayah}...")
    words = get_verse_words(surah, ayah)
    print(f"Words: {len(words)}")
    if words:
        for w in words:
            print(f"Pos {w['position']}: {w['text']}")

if __name__ == "__main__":
    test()
