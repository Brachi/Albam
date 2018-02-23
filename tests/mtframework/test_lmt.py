from ctypes import sizeof
import os

import pytest

from albam.engines.mtframework.lmt import LMT, AnimBlockInfo
from albam.lib.structure import get_offset
from tests.mtframework.conftest import LMT_FILES


@pytest.mark.parametrize('lmt_file', LMT_FILES)
def test_lmt_parsing(lmt_file):
    lmt = LMT(lmt_file)
    block_info_array_size = len(lmt.block_info_array) * sizeof(AnimBlockInfo)
    block_info_array_offset = get_offset(lmt, 'block_info_array')

    assert sizeof(lmt.__class__) == os.path.getsize(lmt_file)
    assert [o for o in lmt.block_offset_array if o] == list(range(block_info_array_offset,
                                                                  block_info_array_offset + block_info_array_size,
                                                                  sizeof(AnimBlockInfo)))
