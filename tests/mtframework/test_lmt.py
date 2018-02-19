from ctypes import sizeof
import os


import pytest

from albam.engines.mtframework.lmt import LMT, AnimBlockInfo
from albam.lib.structure import get_offset
from tests.mtframework.conftest import LMT_FILES


@pytest.mark.parametrize('lmt_file', LMT_FILES)
def test_lmt_parsing(lmt_file):
    lmt = LMT(lmt_file)
    print()
    non_null_offsets = [o for o in lmt.offsets if o]
    first_non_null_offset = non_null_offsets[0]
    assert first_non_null_offset == get_offset(lmt, 'block_info_array')

    for i, offset in enumerate(non_null_offsets):
        if i == 0:
            continue
        assert non_null_offsets[i] - non_null_offsets[i - 1] == sizeof(AnimBlockInfo)

    file_size = os.path.getsize(lmt_file)
    struct_size = sizeof(lmt.__class__)

    print('ID', lmt.ID)
    print('version', lmt.version)
    print('blocks_count', lmt.blocks_count)
    print('file size', file_size)
    print('struct_size', struct_size)
    print('remaining', file_size - struct_size)
    print('----')

    tracks = lmt.decompress()

    for k, v in tracks.items():
        print(k, v)

