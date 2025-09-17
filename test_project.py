import string, re
from project import slugify, next_save_path

def test_slugify():
    def is_ascii_slug(s: str) -> bool:
        return all(ord(c) < 128 for c in s) and all(
            c in string.ascii_lowercase + string.digits + "-" for c in s
        )
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("a---b___c   d") == "a-b-c-d"
    assert slugify("  --Rock & Roll!!  ") == "rock-roll"
    assert slugify("Café com pão ☕️🥐") == "cafe-com-pao"
    assert slugify("Łódź — już!") == "odz-juz"  
    assert slugify("already-slugged") == "already-slugged"
    long = "a" * 50 + " " + "b" * 50
    s = slugify(long, maxlen=60)
    assert len(s) <= 60
    assert not s.endswith("-")
    assert s.startswith("a" * 50)
    assert slugify(None) == "unnamed"
    assert slugify("") == "unnamed"
    assert slugify("", default="none") == "none"
    assert slugify(12345) == "12345"
    assert slugify(0) == "unnamed"
    for val in ["Sharks 🦈", "José Álvaro", "  --X_y.Z  ", "नमस्ते", "中文測試"]:
        out = slugify(val)
        assert is_ascii_slug(out), f"Non-ASCII or invalid chars in slug: {out}"


def test_next_save_path(tmp_path):
    case1 = tmp_path / "case1"
    out = next_save_path(case1, base="game", ext=".json", width=3, create_dir=True)
    assert out.name == "game_001.json"

    case2 = tmp_path / "case2"; case2.mkdir()
    (case2 / "game_001.json").write_text("{}")
    (case2 / "game_003.json").write_text("{}")
    out = next_save_path(case2, base="game", ext=".json", width=3)
    assert out.name == "game_002.json"

    case3 = tmp_path / "case3"; case3.mkdir()
    (case3 / "stats_001.json").write_text("{}")
    (case3 / "game_001.csv").write_text("id\n")
    out = next_save_path(case3, base="game", ext=".json", width=3)
    assert out.name == "game_001.json"

    case4 = tmp_path / "case4"; case4.mkdir()
    (case4 / "game_0001.json").write_text("{}")
    out = next_save_path(case4, base="game", ext=".json", width=4, start=1)
    assert out.name == "game_0002.json"

    case5 = tmp_path / "case5"
    out = next_save_path(case5, base="export", ext="csv", create_dir=True)
    assert out.suffix == ".csv"
    assert out.name == "export_001.csv"

    case6 = tmp_path / "case6" / "nested" / "deeper"
    out = next_save_path(case6, base="game", create_dir=True)
    assert out.parent.exists()
    assert out.name == "game_001.json"

    case7 = tmp_path / "case7"; case7.mkdir()
    (case7 / "game_001.json").write_text("{}")
    (case7 / "game_002.json").write_text("{}")
    out = next_save_path(case7, base="game", max_n=2, timestamp_fallback=True)
    assert out.suffix == ".json"
    assert out.name.startswith("game_")
    assert re.match(r"^game_\d{8}_\d{6}\.json$", out.name)


    
