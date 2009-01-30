#!/usr/bin/env python

import sys
import re
import getopt
import os


class Data:
    def __init__(self, data):
        self.data = data

class DebugData:
    class Item:
        def __init__(self):
            self.type = ''
            self.ref = 0
            self.level = 0
            self.attributes = {}
    def __init__(self, debug_filename):
        file = os.popen ('readelf -wi ' + debug_filename, 'r')
        self.__lines = file.readlines ()
        self.__current = 0
        self.__re1 = re.compile ('<([^>]+)><([^>]+)>:[^A]*Abbrev Number:.*\d+.*\((\w+)\)')
        self.__re2 = re.compile ('<[^>]+>[^D]*(DW_AT_\w+)([^:]*:)+ <?([^ \t><\)]+)[ >\t\)]*$')
        return
    def rewind (self):
        self.__current = 0
        return
    def read_line (self):
        if self.__current == len (self.__lines):
            return ''
        line = self.__lines[self.__current]
        self.__current = self.__current + 1
        return line
    def write_back_line (self):
        self.__current = self.__current - 1
        return
    def write_back_one (self, item):
        self.__current = self.__current - 1 - len (item.attributes.keys ())
        return
    def read_one (self):
        item = DebugData.Item ()
        while 1:
            line = self.read_line ()
            if line == '':
                if item.type == '':
                    return None
                else:
                    return item
            result = self.__re1.search (line)
            if result is None:
                continue
            item.level = result.group (1)
            item.ref = result.group (2)
            item.type = result.group (3)
            while 1:
                line = self.read_line ()
                result = self.__re1.search (line)
                if result is not None:
                    self.write_back_line ()
                    return item
                result = self.__re2.search (line)
                if result is None:
                    self.write_back_line ()
                    return item
                item.attributes[result.group (1)] = result.group (3)
        return item
    def find_struct (self, struct_type_name):
        return self.find_by_name ('DW_TAG_structure_type', struct_type_name)
    def find_by_name (self, type, name):
        item = self.read_one ()
        while item is not None:
            if item.type == type and \
                    item.attributes.has_key ('DW_AT_name') and \
                    item.attributes['DW_AT_name'] == name:
                return item
            item = self.read_one ()
        return item
    def find_by_ref (self, ref):
        item = self.read_one ()
        while item is not None:
            if item.ref == ref:
                return item
            item = self.read_one ()
        return item
    def find_member (self, member_name, parent):
        sub_item = self.read_one ()
        while sub_item is not None:
            if sub_item.level == parent.level:
                self.write_back_one ()
                return None
            if sub_item.type == 'DW_TAG_member' and \
                    sub_item.attributes.has_key ('DW_AT_name') and \
                    sub_item.attributes['DW_AT_name'] == member_name:
                return Data (sub_item.attributes['DW_AT_data_member_location'])
            sub_item = self.read_one ()
        return None
    # public methods below
    def get_struct_member_offset (self, struct_type_name, member_name):
        self.rewind ()
        item = self.find_struct (struct_type_name)
        if item is None:
            return None
        return self.find_member (member_name, item)
    def get_struct_size (self, struct_type_name):
        self.rewind ()
        item = self.find_struct (struct_type_name)
        if item is None:
            return None
        if not item.attributes.has_key ('DW_AT_byte_size'):
            return None
        return Data (item.attributes['DW_AT_byte_size'])    
    def get_typedef_member_offset (self, typename, member):
        self.rewind ()
        item = self.find_by_name ('DW_TAG_typedef', typename)
        if item is None:
            return None
        if not item.attributes.has_key ('DW_AT_type'):
            return None
        ref = item.attributes['DW_AT_type']
        self.rewind ()
        item = self.find_by_ref (ref)
        if item is None:
            return None
        return self.find_member (member, item)

        
def usage():
    print ''

def main(argv):
    config_filename = ''
    debug_filename = ''
    try:
        opts, args = getopt.getopt(argv, 'hc:d:',
                                   ['help', 'config=', 'debug='])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-c', '--config'):
            config_filename = arg
        elif opt in ('-d', '--debug'):
            debug_filename = arg

    debug = DebugData (debug_filename)
    config = open (config_filename, 'w')
    data = debug.get_struct_size ('rtld_global')
    if data is None:
        sys.exit (1)
    config.write ('#define CONFIG_RTLD_GLOBAL_SIZE ' + str(data.data) + '\n')

    data = debug.get_struct_size ('rtld_global_ro')
    if data is None:
        sys.exit (1)
    config.write ('#define CONFIG_RTLD_GLOBAL_RO_SIZE ' + str(data.data) + '\n')

    data = debug.get_struct_member_offset ('rtld_global', '_dl_error_catch_tsd')
    if data is None:
        sys.exit (1)
    config.write ('#define CONFIG_DL_ERROR_CATCH_TSD_OFFSET ' + str(data.data) + '\n')

    data = debug.get_struct_size ('pthread')
    if data is None:
        sys.exit (1)
    config.write ('#define CONFIG_TCB_SIZE ' + str(data.data) + '\n')

    data = debug.get_typedef_member_offset ('tcbhead_t', 'tcb')
    if data is None:
        sys.exit (1)
    config.write ('#define CONFIG_TCB_TCB_OFFSET ' + str(data.data) + '\n')

    data = debug.get_typedef_member_offset ('tcbhead_t', 'dtv')
    if data is None:
        sys.exit (1)
    config.write ('#define CONFIG_TCB_DTV_OFFSET ' + str(data.data) + '\n')

    data = debug.get_typedef_member_offset ('tcbhead_t', 'self')
    if data is None:
        sys.exit (1)
    config.write ('#define CONFIG_TCB_SELF_OFFSET ' + str(data.data) + '\n')

    data = debug.get_typedef_member_offset ('tcbhead_t', 'sysinfo')
    if data is None:
        sys.exit (1)
    config.write ('#define CONFIG_TCB_SYSINFO_OFFSET ' + str(data.data) + '\n')

if __name__ == "__main__":
    main(sys.argv[1:])





