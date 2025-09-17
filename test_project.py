import string
from project import slugify

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
