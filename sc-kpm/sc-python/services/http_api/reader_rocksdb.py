import multiprocessing
import struct

from sc import *
from common import *

import rocksdb
import time
import concurrent.futures

from progress.bar import IncrementalBar


class RocksdbReader():
    addr_postfix = "_addrs"
    long_content = None

    def __init__(self, _ctx, _keynodes):
        self.ctx = _ctx
        self.keynodes = _keynodes
        self.sys = []
        self.main = []
        self.common = []
        self.addr = []
        self.long_content_counter = 0
        self.content_len_max = 200

    def read_rocksdb(self, rocksdb_fm_path):
        """read db and fill self.sys, self.main and self.common lists by addrs"""
        print("Reading db ...")

        time_start = time.perf_counter()

        opts = rocksdb.Options()
        opts.create_if_missing = False
        opts.compression = rocksdb.CompressionType.snappy_compression
        rdb = rocksdb.DB(rocksdb_fm_path, opts, read_only=True)
        it = rdb.iteritems()
        it.seek_to_first()
        items = list(it)

        for item in items:
            self.form_addr_list(item)

        optimal_threads_count = 2 * multiprocessing.cpu_count() + 1
        languages = self.get_languages()
        with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_threads_count) as executor:
            future_sort = {executor.submit(self.sorter, languages, addr): addr for addr in self.addr}

        time_end = time.perf_counter()
        time_taken = round(time_end - time_start, 2)
        loaded_elems = len(self.sys) + len(self.main) + len(self.common)
        print(f"{loaded_elems} elems loaded in {time_taken} second(s)")

    def form_addr_list(self, item):
        """fill self.addr list by addrs from db"""
        key = item[0].decode('utf-8')
        if key.endswith(self.addr_postfix):
            val = item[1]
            encoded_addrs = val[8:]
            addrs_count = val[0]
            byte_border = 0
            for _ in range(addrs_count):
                try:
                    seg, offset = struct.unpack('=HH', encoded_addrs[byte_border: byte_border + 4])
                    self.addr.append(ScAddr((seg << 16 | offset)))
                except:
                    self.addr.append(None)
                byte_border += 4

    def get_languages(self):
        return [self.keynodes['lang_en'], self.keynodes['lang_ru']]

    def sorter(self, languages: list, node_addr: ScAddr):
        link_content = self.ctx.GetLinkContent(node_addr)
        if link_content is None:
            return
        link_content_decoded = link_content.AsString()
        nrel_sys_idtf = self.keynodes['nrel_system_identifier']
        nrel_main_idtf = self.keynodes['nrel_main_idtf']
        nrel_idtf = self.keynodes['nrel_idtf']
        idtf_iter = self.ctx.Iterator5(
            ScType.Unknown,
            ScType.EdgeDCommonConst,
            node_addr,
            ScType.EdgeAccessConstPosPerm,
            nrel_sys_idtf
        )
        if idtf_iter.Next():
            self.sys.append([idtf_iter.Get(0).ToInt(), link_content_decoded])
            return
        if len(link_content_decoded.encode('utf-8')) > 200:
            return
        for lang in languages:
            idtf_addr = None
            sys_idtf_iter = self.ctx.Iterator5(
                ScType.Unknown,
                ScType.EdgeDCommonConst,
                node_addr,
                ScType.EdgeAccessConstPosPerm,
                nrel_main_idtf
            )
            idtf_iter = self.ctx.Iterator5(
                ScType.Unknown,
                ScType.EdgeDCommonConst,
                node_addr,
                ScType.EdgeAccessConstPosPerm,
                nrel_idtf
            )
            if sys_idtf_iter.Next():
                lang_iter = self.ctx.Iterator3(lang, ScType.EdgeAccessConstPosPerm, node_addr)
                if lang_iter.Next():
                    idtf_addr = sys_idtf_iter.Get(0)
            elif idtf_iter.Next():
                lang_iter = self.ctx.Iterator3(lang, ScType.EdgeAccessConstPosPerm, node_addr)
                if lang_iter.Next():
                    idtf_addr = idtf_iter.Get(0)
            if idtf_addr is not None:
                self.main.append([idtf_addr.ToInt(), link_content_decoded])
            else:
                self.common.append([node_addr.ToInt(), link_content_decoded])

    def update(self):
        # call after changing db
        # should update lists for searching new elems
        pass

