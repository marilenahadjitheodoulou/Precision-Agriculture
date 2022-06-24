#Balestra, Malaguti

import xmlschema
import struct
import copy
import datetime
import functools
import json
import os.path

import utils

DEFAULT_ISO_SCHEMA = 'schemas/ISO11783_TaskFile_V3-3.xsd'


def write_bin_grd( numgrd, grid, path='.'):
    filename = 'GRD' + str(numgrd).zfill(5)
    if not grid:
        return filename
    with open('%s/%s.bin'%(path, filename), 'w+b') as f:
        [f.write(int(value).to_bytes(4, byteorder='little', signed=True)) for value in grid]
    return filename

def read_bin_tlg(filename, path='.', vocabulary=True, xsd = DEFAULT_ISO_SCHEMA):
    # unpack format map
    bin_type_map = {'TIM': {'A': 'IH'},
                    'PTN': {'A': 'i',
                            'B': 'i',
                            'C': 'i',
                            'D': 'B',
                            'E': 'H',
                            'F': 'H',
                            'G': 'B',
                            'H': 'I',
                            'I': 'H'},
                    'DLV': {'#': 'B',
                            'n': 'B',
                            'B': 'I',
                            'C': 'I'}
                    }
    
    
    def get_conversion_func(tag, attribute):
        # conversion type map
        get_datetime=(lambda date,days_index,milliseconds_index:(datetime.datetime(1980, 1, 1)+ datetime.timedelta(date[days_index], 0, 0, date[milliseconds_index])).isoformat())
        get_scaled=(lambda raw,factor: sum(raw)*factor)
        type_conversion_map = { 
            'TIM': {'A': functools.partial(get_datetime, days_index=1, milliseconds_index=0)},
            'PTN': {'A': functools.partial(get_scaled, factor=1e-7),
                    'B': functools.partial(get_scaled, factor=1e-7),
                    'C': functools.partial(get_scaled, factor=1e-3),
                    'E': functools.partial(get_scaled, factor=1e-1),
                    'F': functools.partial(get_scaled, factor=1e-1),
            }
        }
        try:
            return type_conversion_map[tag][attribute]
        except KeyError:
            # reduce the touple tag
            return sum

    def recursive_byte_row(root, fmt='=', *args):
        args=list(args)
        for k,v in root.items():
            if k.startswith('@') and not v:
                fmt+=functools.reduce(dict.get, args+[k[1:],], bin_type_map)
            elif isinstance(v, dict):
                fmt+=recursive_byte_row(v,'',*(args+ [k,]))
            elif isinstance(v, list):
                fmt+=''.join([recursive_byte_row(item,'',*(args+[k,])) for item in v])
        return fmt
    
    if os.path.exists(os.path.join(path, filename+'.xml')):
        filename_xlm = os.path.join(path, filename+'.xml')
    elif os.path.exists(os.path.join(path, filename+'.XML')):
        filename_xlm = os.path.join(path, filename+'.XML')
    else:
        raise Exception('xml file %s not found'%filename)

    if os.path.exists(os.path.join(path, filename+'.bin')):
        filename_bin = os.path.join(path, filename+'.bin')
    elif os.path.exists(os.path.join(path, filename+'.BIN')):
        filename_bin = os.path.join(path, filename+'.BIN')
    else:
        raise Exception('bin file %s not found'%filename)

    schema = xmlschema.XMLSchema(xsd, validation='skip')
    root_tag = 'TIM'
    proto = dict(TIM = schema.to_dict(xmlschema.XMLResource(filename_xlm), validation='skip'))

    expected = [{'tag': root_tag, 'attr': a[1:], 'pos': None} for a, y in proto[root_tag].items()
                if y == '' and a[0] == '@']

    expected.extend([{'tag': 'PTN', 'attr': a[1:], 'pos': i} for i, x in enumerate(proto[root_tag]['PTN'])
                        for a, y in x.items() if y == ''])

    try:
        expected_dlv = {i: [{'tag': 'DLV', 'attr': a[1:], 'pos': i} for a, y in x.items() if y == '']
                    for i, x in enumerate(proto[root_tag]['DLV'])}
    except Exception:
        return []

    expected.append({'tag': 'DLV', 'attr': '#', 'pos': None})

    upattern = ''.join([bin_type_map[x['tag']][x['attr']] for x in expected])
    
    data = []
    with open(filename_bin, "rb") as f:
        while True:
            try:
                actual = copy.deepcopy(proto)
                chunk = f.read(struct.calcsize('=' + upattern))
                if chunk:
                    # read the fixed amount of data (root attributes + PTN(s) attributes + DLV#)
                    fixed_bin_data = struct.unpack("=" + upattern, chunk)

                    offset = 0
                    # scam list for values and mapping
                    for data_item in expected:
                        num_elem = len(bin_type_map[data_item['tag']][data_item['attr']])

                        translate = get_conversion_func(data_item['tag'], data_item['attr'])
                        value = translate(fixed_bin_data[offset:offset + num_elem])

                        offset += num_elem
                        # prefix '@' is for XML attribute keys in xmlschema dict representation
                        if data_item['tag'] == root_tag:
                            actual[root_tag]['@' + data_item['attr']] = value
                        elif data_item['pos'] is not None:
                            actual[root_tag][data_item['tag']][data_item['pos']]['@' + data_item['attr']] = value

                    # number of following DLVs elements DLV# = fixed_bin_data[-1]
                    for i in range(fixed_bin_data[-1]):
                        dpattern = "=B" + ''.join([bin_type_map[x['tag']][x['attr']] for x in expected_dlv[i]])
                        chunki = f.read(struct.calcsize(dpattern))

                        dlv_bin_data = struct.unpack(dpattern, chunki)

                        offset = 1
                        for data_item in expected_dlv[i]:
                            num_elem = len(bin_type_map[data_item['tag']][data_item['attr']])

                            translate = get_conversion_func(data_item['tag'], data_item['attr'])
                            value = translate(dlv_bin_data[offset:offset + num_elem])

                            offset += num_elem

                            if data_item['pos'] is not None:
                                # data is an actual value
                                # DLV position index is given in the binary stream dlv_bin_data[0]
                                if actual[root_tag][data_item['tag']][dlv_bin_data[0]] is not None:
                                    actual[root_tag][data_item['tag']][dlv_bin_data[0]]['@' + data_item['attr']] \
                                        = value

                    # remove from structure DLVs not present in the binary sequence
                    if fixed_bin_data[-1] < len(expected_dlv):
                        actual[root_tag]['DLV'] = [x for x in actual[root_tag]['DLV'] if '' not in x.values()]

                    # list representation of xmlschema
                    data.append(actual[root_tag])
                else:
                    break
            except KeyError as error:
                # binary data is corrupted (DLV index is out of bounds)
                # TODO
                # should rise a custom error?
                raise error
            except struct.error as error:
                # binary file is not well formatted/made
                # TODO
                # should rise a custom error?
                raise error
    
    if vocabulary:
        xsd_vocabulary = utils.make_vocabulary(xsd)
        # insert root_tag just for allowing attribute key-names conversion of the root tag itself
        data_named = utils.replace_keys({root_tag: data}, '', xsd_vocabulary)
        return data_named[xsd_vocabulary[root_tag]]

    return data

if __name__ == '__main__':
    testfile = 'TLG00001'

    res = read_bin_tlg(testfile)
    from pprint import pprint
    pprint(res)
