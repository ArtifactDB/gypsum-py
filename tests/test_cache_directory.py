import gypsum_client
import tempfile
import os


def test_cache_directory():
    cache_dir = gypsum_client.cache_directory()
    assert isinstance(cache_dir, str)

    tdir = os.path.join(tempfile.mkdtemp(), "foobar")
    cache_dir2 = gypsum_client.cache_directory(tdir)
    assert cache_dir == cache_dir2

    cache_dir3 = gypsum_client.cache_directory()
    assert cache_dir3 == tdir

    gypsum_client.cache_directory(cache_dir)
    assert gypsum_client.cache_directory() == cache_dir
