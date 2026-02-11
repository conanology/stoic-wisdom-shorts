"""Quick sanity check for all Stoic Wisdom modules"""
import sys

def test_quotes_api():
    print("Testing quotes_api...", end=" ")
    from core.quotes_api import get_quotes_manager
    m = get_quotes_manager()
    total = m.get_total_quotes()
    assert total > 0, "No quotes loaded"
    keys = m.get_philosopher_keys()
    assert len(keys) > 0, "No philosophers loaded"
    q = m.get_quote_by_index(0)
    assert q is not None, "First quote is None"
    fmt = m.format_for_video(q)
    assert "quote_text" in fmt
    assert "author_name" in fmt
    print(f"OK ({total} quotes, {len(keys)} philosophers)")
    print(f"  First: \"{fmt['quote_text'][:50]}...\" — {fmt['author_name']}")

def test_database():
    print("Testing database...", end=" ")
    from database.models import init_database, get_db_session, QuoteProgress
    init_database()
    session = get_db_session()
    # Just ensure we can query
    result = session.query(QuoteProgress).first()
    session.close()
    print("OK (tables created)")

def test_quote_scheduler():
    print("Testing quote_scheduler...", end=" ")
    from core.quote_scheduler import get_current_progress, get_next_quote
    progress = get_current_progress()
    assert "current_index" in progress
    assert "total_quotes" in progress
    q = get_next_quote()
    assert "quote_text" in q
    assert "author_name" in q
    print(f"OK (position {progress['current_index']}/{progress['total_quotes']})")

def test_tts_engine():
    print("Testing tts_engine...", end=" ")
    from core.tts_engine import TTSEngine
    engine = TTSEngine()
    print(f"OK (voice={engine.voice})")

def test_style_config():
    print("Testing style_config...", end=" ")
    from core.style_config import DEFAULT_STYLE
    assert DEFAULT_STYLE.video_width == 1080
    assert DEFAULT_STYLE.video_height == 1920
    print("OK")

def test_settings():
    print("Testing config/settings...", end=" ")
    from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT, CHANNEL_NAME
    assert VIDEO_WIDTH == 1080
    assert VIDEO_HEIGHT == 1920
    assert CHANNEL_NAME == "Stoic Wisdom"
    print(f"OK (channel={CHANNEL_NAME})")

def test_text_renderer():
    print("Testing text_renderer...", end=" ")
    from core.text_renderer import create_quote_clip
    # Just verify the function exists and is callable
    assert callable(create_quote_clip)
    print("OK")

def test_main_cli():
    print("Testing main CLI...", end=" ")
    import main
    assert hasattr(main, 'cmd_generate')
    assert hasattr(main, 'cmd_auto')
    assert hasattr(main, 'cmd_status')
    print("OK")

if __name__ == "__main__":
    print("=" * 50)
    print("Stoic Wisdom Shorts — Module Sanity Check")
    print("=" * 50)
    
    tests = [
        test_settings,
        test_quotes_api,
        test_database,
        test_quote_scheduler,
        test_tts_engine,
        test_style_config,
        test_text_renderer,
        test_main_cli,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL: {e}")
            failed += 1
    
    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All checks passed! ✅")
    else:
        print("Some checks failed ❌")
        sys.exit(1)
