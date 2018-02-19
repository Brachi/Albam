from collections import defaultdict
from ctypes import Structure, sizeof, c_uint, c_float, c_ushort, c_ubyte, addressof, c_longlong

from albam.lib.structure import DynamicStructure, get_offset


def get_padding(structure):
    # TODO: figure out the rule
    first_non_null_offset = [o for o in structure.offsets if o][0]
    diff = first_non_null_offset - sizeof(structure)
    if diff:
        return c_ubyte * abs(diff)
    return c_ubyte * 0


def get_block_info_array(structure):
    non_null_offsets = [o for o in structure.offsets if o]
    return AnimBlockInfo * len(non_null_offsets)


def get_frames(structure):
    total_frames = 0
    for block in structure.block_info_array:
        frames_count = block.bone_count * block.frame_count
        total_frames += frames_count
    return AnimFrame * total_frames


def get_buffer(structure):
    total_size = sum(frame.buffer_size for frame in structure.frames)
    return c_ubyte * total_size


def get_unknown_buffer(structure):
    total_size = 0
    for block in structure.block_info_array:
        unk_start = block.unk_01[26]
        unk_end = block.unk_01[-1]
        size = unk_end - unk_start
        total_size += size

    return c_ubyte * total_size


class AnimBlockInfo(Structure):

    _fields_ = (('offset', c_uint),
                ('bone_count', c_uint),
                ('frame_count', c_uint),
                ('unk_01', c_uint * 45))


class LMTVec3Frame(Structure):
    _fields_ = (('x', c_float),
                ('y', c_float),
                ('z', c_float)
                )

    def decompress(self):
        return self.x, self.y, self.z


class LMTQuatFramev14(Structure):
    _fields_ = (('i_value', c_longlong),
                #('i_value_2', c_float),
                )

    def decompress(self):
        pow_14 = (2 ** 14) - 1
        src = self.i_value

        num = src & pow_14
        if num > 8191:
            num -= pow_14
        real = num / 4096

        num = (src >> 14) & pow_14
        if num > 8191:
            num -= pow_14
        k = num / 4096

        num = ((src >> 14) >> 14) & pow_14
        if num > 8191:
            num -= pow_14
        j = num / 4096

        num = (((src >> 14) >> 14) >> 14) & pow_14
        if num > 8191:
            num -= pow_14
        i = num / 4096

        return (real, i, j, k)


class AnimFrame(Structure):

    _fields_ = (('buffer_type', c_ubyte),
                ('usage', c_ubyte),
                ('joint_type', c_ubyte),
                ('bone_index', c_ubyte),
                ('unk_01', c_float),
                ('buffer_size', c_uint),
                ('buffer_offset', c_uint),
                ('reference_data', c_float * 4),
                )


class LMT(DynamicStructure):

    _fields_ = (('ID', c_uint,),
                ('version', c_ushort),
                ('blocks_count', c_ushort),
                ('offsets', lambda s: (s.blocks_count) * c_uint),
                ('padding', get_padding),
                ('block_info_array', get_block_info_array),
                ('frames', get_frames),
                ('buffer', get_buffer),
                #  ('unk_buffer', get_unknown_buffer)
                )

    def decompress(self):
        """
        Return a dict with bone ids as keys and a dict of tracks:
            {<bone_id>: {'rotation': [<frame_1>, <frame_2>, ...]
                         'location': [<frame_1>, <frame_2>, ...]
                         }
           }
           where a frame in rotation is a tuple of w,x,y,z values (quaternions)
           and a frame in location is ?
        """
        tracks = defaultdict(lambda: {'rotation': [],
                                      'location': [],
                                      'location_ik': [],
                                      'rotation_ik': [],
                             })

        buffer_address = addressof(self.buffer)
        for frame in self.frames:
            relative_start = frame.buffer_offset - get_offset(self, 'buffer')
            address = buffer_address + relative_start
            data_type = None
            if frame.buffer_type != 6:
                print(frame.bone_index, frame.buffer_type, frame.usage, frame.joint_type)
            if frame.buffer_type == 6:
                cls = LMTQuatFramev14
                data_type = 'rotation'
            elif frame.buffer_type == 2:
                cls = LMTVec3Frame
                data_type = 'location_ik'
            else:
                print('unsupported buffer_type', frame.buffer_type)
                continue
            data = cls.from_address(address).decompress()
            tracks[frame.bone_index][data_type].append(data)
            #if data_type == 'location_ik':
            #    tracks[frame.bone_index]['rotation_ik'].append(tuple(frame.reference_data[0:3]))
        return tracks
