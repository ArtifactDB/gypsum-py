import json
import sqlite3
import tempfile

from gypsum_client import define_text_query, search_metadata_text

__author__ = "Jayaram Kancherla, chatGPT"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

sqlite_path = tempfile.mkdtemp() + "/test.sqlite"


def setup_database():
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    cur.execute(
        """CREATE TABLE versions (
        vid INTEGER PRIMARY KEY,
        project TEXT,
        asset TEXT,
        version TEXT,
        latest BOOLEAN
    )"""
    )

    cur.execute(
        """CREATE TABLE paths (
        pid INTEGER PRIMARY KEY,
        vid INTEGER,
        path TEXT,
        metadata TEXT
    )"""
    )

    cur.execute(
        """CREATE TABLE tokens (
        tid INTEGER PRIMARY KEY,
        token TEXT
    )"""
    )

    cur.execute(
        """CREATE TABLE fields (
        fid INTEGER PRIMARY KEY,
        field TEXT
    )"""
    )

    cur.execute(
        """CREATE TABLE links (
        pid INTEGER,
        fid INTEGER,
        tid INTEGER
    )"""
    )

    versions = [
        (1, "foo", "bar", "1", False),
        (2, "foo", "bar", "2", False),
        (3, "foo", "bar", "3", True),
    ]
    cur.executemany("INSERT INTO versions VALUES (?, ?, ?, ?, ?)", versions)

    metadata = [
        {
            "first_name": "mikoto",
            "last_name": "misaka",
            "school": "tokiwadai",
            "ability": "railgun",
            "gender": "female",
            "comment": "rank 3",
        },
        {
            "first_name": "mitsuko",
            "last_name": "kongou",
            "school": "tokiwadai",
            "ability": "aerohand",
            "gender": "female",
        },
        {
            "first_name": "kuroko",
            "last_name": "shirai",
            "school": "tokiwadai",
            "ability": "teleport",
            "gender": "female",
            "affiliation": "judgement",
        },
        {
            "first_name": "misaki",
            "last_name": "shokuhou",
            "school": "tokiwadai",
            "ability": "mental out",
            "gender": "female",
            "comment": "rank 5",
        },
        {
            "first_name": "ruiko",
            "last_name": "saten",
            "school": "sakugawa",
            "gender": "female",
        },
        {
            "first_name": "kazari",
            "last_name": "uiharu",
            "school": "sakugawa",
            "gender": "female",
            "affiliation": "judgement",
        },
        {
            "first_name": "accelerator",
            "ability": "vector manipulation",
            "gender": "male",
            "comment": "rank 1",
        },
    ]

    paths = [
        (
            i + 1,
            (i % 3) + 1,
            f'{metadata[i]["first_name"]}.txt',
            json.dumps(metadata[i]),
        )
        for i in range(len(metadata))
    ]
    cur.executemany("INSERT INTO paths VALUES (?, ?, ?, ?)", paths)

    all_tokens = list(
        set(
            token
            for item in metadata
            for token in item.values()
            if isinstance(token, str)
            for token in token.split()
        )
    )
    cur.executemany(
        "INSERT INTO tokens (token) VALUES (?)", [(token,) for token in all_tokens]
    )

    all_fields = list(set(key for item in metadata for key in item.keys()))
    cur.executemany(
        "INSERT INTO fields (field) VALUES (?)", [(field,) for field in all_fields]
    )

    links = []
    for i, item in enumerate(metadata):
        for field, value in item.items():
            if isinstance(value, str):
                tokens = set(value.split())
                pid = i + 1
                fid = all_fields.index(field) + 1
                for token in tokens:
                    tid = all_tokens.index(token) + 1
                    links.append((pid, fid, tid))
    cur.executemany("INSERT INTO links VALUES (?, ?, ?)", links)

    conn.commit()
    conn.close()


setup_database()


def test_search_metadata_text_text_searches():
    result = search_metadata_text(
        sqlite_path, ["mikoto"], include_metadata=False, latest=False
    )

    assert len(result) == 1
    assert result[0]["path"] == "mikoto.txt"

    result = search_metadata_text(
        sqlite_path, ["kuroko"], include_metadata=False, latest=False
    )
    assert len(result) == 1
    assert result[0]["path"] == "kuroko.txt"

    result = search_metadata_text(
        sqlite_path, ["TOKIWADAI"], include_metadata=False, latest=False
    )
    assert len(result) == 4

    paths = [r["path"] for r in result]
    assert sorted(paths) == sorted(
        ["mikoto.txt", "mitsuko.txt", "kuroko.txt", "misaki.txt"]
    )


def test_search_metadata_text_and_searches():
    result = search_metadata_text(
        sqlite_path, ["sakugawa", "judgement"], include_metadata=False, latest=False
    )
    assert len(result) == 1
    assert result[0]["path"] == "kazari.txt"

    query = define_text_query("sakugawa") & define_text_query("judgement")
    result = search_metadata_text(
        sqlite_path, query, include_metadata=False, latest=False
    )
    assert len(result) == 1
    assert result[0]["path"] == "kazari.txt"


def test_search_metadata_text_or_searches():
    query = define_text_query("uiharu") | define_text_query("rank")
    result = search_metadata_text(
        sqlite_path, query, include_metadata=False, latest=False
    )
    assert len(result) == 4

    paths = [r["path"] for r in result]
    assert sorted(paths) == sorted(
        ["mikoto.txt", "kazari.txt", "accelerator.txt", "misaki.txt"]
    )


def test_search_metadata_text_not_searches():
    query = ~define_text_query("uiharu")
    result = search_metadata_text(
        sqlite_path, query, include_metadata=False, latest=False
    )
    assert len(result) == 6

    paths = [r["path"] for r in result]
    assert sorted(paths) == sorted(
        [
            "mikoto.txt",
            "accelerator.txt",
            "misaki.txt",
            "mitsuko.txt",
            "kuroko.txt",
            "ruiko.txt",
        ]
    )


def test_search_metadata_text_combined_and_or_searches():
    result = search_metadata_text(
        sqlite_path, ["judgement", "sakugawa"], include_metadata=False, latest=False
    )
    assert len(result) == 1
    assert result[0]["path"] == "kazari.txt"


def test_search_metadata_text_respects_output_options():
    result = search_metadata_text(
        sqlite_path, ["female"], include_metadata=True, latest=False
    )
    assert len(result) == 6
