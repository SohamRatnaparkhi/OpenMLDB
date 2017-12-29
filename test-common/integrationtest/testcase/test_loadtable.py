# -*- coding: utf-8 -*-
import unittest
from testcasebase import TestCaseBase
import time
import threading
import xmlrunner
from libs.test_loader import load
from libs.logger import infoLogger
from libs.deco import multi_dimension


class TestLoadTable(TestCaseBase):

    def test_loadtable_newleader_success_can_put(self):
        """
        拷贝db目录后loadtable，功能正常
        新节点是主节点，loadtable后可以put数据
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 6):
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey',
                     self.now() - i,
                     'testvalue')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        # 新主节点loadtable后可以put数据
        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid, 144000, 8, 'true')
        self.assertTrue('LoadTable ok' in rs3)
        table_status = self.get_table_status(self.slave1, self.tid, self.pid)
        self.assertEqual(table_status, ['6', 'kTableLeader', 'kTableNormal', 'true', '144000min', '0s'])

        # for multidimension test
        self.multidimension_vk = {'card': ('string:index', 'testkey111'),
                                  'merchant': ('string:index', 'testvalue111'),
                                  'amt': ('double', 1.1)}
        self.multidimension_scan_vk = {'card': 'testkey111'}

        rs4 = self.put(self.slave1,
                       self.tid,
                       self.pid,
                       'testkey111',
                       self.now(),
                       'testvalue111')
        self.assertTrue('Put ok' in rs4)
        self.assertTrue(
            'testvalue111' in self.scan(self.slave1, self.tid, self.pid, 'testkey111', self.now(), 1))


    def test_loadtable_newslave_success_cannot_put(self):
        """
        拷贝db目录后loadtable，功能正常
        新节点是从节点，loadtable后不可以put数据
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 6):
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey',
                     self.now() - i,
                     'testvalue')
        time.sleep(1)
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        # 新从节点loadtable后不可以put数据
        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)
        table_status = self.get_table_status(self.slave1, self.tid, self.pid)
        self.assertEqual(table_status, ['6', 'kTableFollower', 'kTableNormal', 'true', '144000min', '0s'])

        # for multidimension test
        self.multidimension_vk = {'card': ('string:index', 'testkey111'),
                                  'merchant': ('string:index', 'testvalue111'),
                                  'amt': ('double', 1.1)}
        rs4 = self.put(self.slave1,
                       self.tid,
                       self.pid,
                       'testkey111',
                       self.now(),
                       'testvalue111')
        self.assertTrue('Put failed' in rs4)

        self.multidimension_scan_vk = {'card': 'testkey111'}  # for multidimension test
        self.assertFalse(
            'testvalue111' in self.scan(self.slave1, self.tid, self.pid, 'testkey111', self.now(), 1))


    def test_loadtable_failed_after_drop(self):
        """
        drop表后可以重新loadtable
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 3):
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey',
                     self.now() - i,
                     'testvalue')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        rs3 = self.drop(self.leader, self.tid, self.pid)
        self.assertTrue('Drop table ok' in rs3)
        rs4 = self.loadtable(self.leader, 't', self.tid, self.pid, 144000, 8, 'true')
        self.assertFalse('Fail' not in rs4)


    @multi_dimension(False)
    def test_loadtable_andthen_sync_from_leader(self):
        """
        从节点loadtable后可以同步主节点后写入的数据
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid, 144000, 8, 'true', self.slave1)
        self.assertTrue('Create table ok' in rs1)
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'k1',
                 self.now(),
                 'v1')
        time.sleep(1)

        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid, 144000, 8, 'false', self.slave1)
        self.assertTrue('LoadTable ok' in rs3)

        table_status = self.get_table_status(self.slave1, self.tid, self.pid)
        self.assertEqual(table_status, ['1', 'kTableFollower', 'kTableNormal', 'true', '144000min', '0s'])

        rs4 = self.put(self.leader,
                       self.tid,
                       self.pid,
                       'k2',
                       self.now(),
                       'v2')
        self.assertTrue('Put ok' in rs4)
        time.sleep(1)

        table_status = self.get_table_status(self.slave1, self.tid, self.pid)
        self.assertEqual(table_status, ['2', 'kTableFollower', 'kTableNormal', 'true', '144000min', '0s'])
        self.assertTrue('v1' in self.scan(self.slave1, self.tid, self.pid, 'k1', self.now(), 1))
        self.assertTrue('v2' in self.scan(self.slave1, self.tid, self.pid, 'k2', self.now(), 1))


    @multi_dimension(True)
    def test_loadtable_andthen_sync_from_leader_md(self):
        """
        从节点loadtable后可以同步主节点后写入的数据
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid, 144000, 8, 'true')
        self.assertTrue('Create table ok' in rs1)
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 '',
                 self.now(),
                 'v1', '1.1', 'k1')
        time.sleep(1)

        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid, 144000, 8, 'false')
        self.assertTrue('LoadTable ok' in rs3)

        rs4 = self.addreplica(self.leader, self.tid, self.pid, 'client', self.slave1)
        self.assertTrue('AddReplica ok' in rs4)

        table_status = self.get_table_status(self.slave1, self.tid, self.pid)
        self.assertEqual(table_status, ['1', 'kTableFollower', 'kTableNormal', 'true', '144000min', '0s'])

        rs3 = self.put(self.leader,
                       self.tid,
                       self.pid,
                       '',
                       self.now(),
                       'v2', '1.1', 'k2')
        self.assertTrue('Put ok' in rs3)
        time.sleep(1)

        table_status = self.get_table_status(self.slave1, self.tid, self.pid)
        self.assertEqual(table_status, ['2', 'kTableFollower', 'kTableNormal', 'true', '144000min', '0s'])
        self.assertTrue('v1' in self.scan(self.slave1, self.tid, self.pid, {'card':'k1'}, self.now(), 1))
        self.assertTrue('v2' in self.scan(self.slave1, self.tid, self.pid, {'card':'k2'}, self.now(), 1))


    @multi_dimension(False)
    def test_loadtable_ttl_removed_expired_key(self):
        """
        节点1 插入部分过期数据，makesnapshot
        拷贝db目录到节点2
        节点2 loadtable时会剔除过期的key
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 6):
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey{}'.format(i),
                     self.now() - (100000000000 * (i % 2) + 1),
                     'testvalue{}'.format(i))
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)
        time.sleep(3)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)

        # 未过期key可以scan出来，过期key scan不出来
        self.assertTrue('testvalue0' in self.scan(self.slave1, self.tid, self.pid, 'testkey0', self.now(), 1))
        self.assertFalse('testvalue1' in self.scan(self.slave1, self.tid, self.pid, 'testkey1', self.now(), 1))

        table_status = self.get_table_status(self.leader, self.tid, self.pid)
        self.assertEqual(table_status, ['6', 'kTableLeader', 'kTableNormal', 'true', '144000min', '0s'])


    @multi_dimension(True)
    def test_loadtable_ttl_removed_expired_key_md(self):
        """
        节点1 插入部分过期数据，makesnapshot
        拷贝db目录到节点2
        节点2 loadtable时会剔除过期的key
        :return:
        """
        kv = {'card': ('string:index', ''), 'card2': ('string', '')}
        self.create(self.leader, 't', self.tid, self.pid, 144000, 2, 'true', **{k: v[0] for k, v in kv.items()})
        for i in range(6):
            kv = {'card': ('string:index', 'card' + str(i)), 'card2': ('string', 'value' + str(i))}
            self.put(self.leader, self.tid, self.pid, '',
                     self.now() - (100000000000 * (i % 2) + 1),
                     *[str(v[1]) for v in kv.values()])
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)
        time.sleep(3)

        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)

        # 未过期key可以scan出来，过期key scan不出来
        self.assertTrue('value0' in self.scan(self.slave1, self.tid, self.pid, {'card': 'card0'}, self.now(), 1))
        self.assertFalse('value1' in self.scan(self.slave1, self.tid, self.pid, {'card': 'card1'}, self.now(), 1))

        table_status = self.get_table_status(self.leader, self.tid, self.pid)
        self.assertEqual(table_status, ['6', 'kTableLeader', 'kTableNormal', 'true', '144000min', '0s'])


    def test_loadtable_ttl_zero(self):
        """
        ttl为0，loadtable时可以load所有数据，无过期
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid, 0)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 3):
            # for multidimension test
            self.multidimension_vk = {'card': ('string:index', 'testkey{}'.format(i)),
                                      'merchant': ('string:index', 'testvalue{}'.format(i)),
                                      'amt': ('double', 1.1)}
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey{}'.format(i),
                     self.now() - 100000000000,
                     'testvalue{}'.format(i))
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid, 0)
        self.assertTrue('LoadTable ok' in rs3)

        # 所有数据不过期，全部scan出来
        for i in range(0, 3):
            self.multidimension_scan_vk = {'card': 'testkey{}'.format(i)}  # for multidimension test
            rs = self.scan(self.slave1, self.tid, self.pid, 'testkey{}'.format(i), self.now(), 1)
            self.assertTrue('testvalue{}'.format(i) in rs)


    def test_loadtable_failed_table_exist(self):
        """
        table已存在，不允许loadtable
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'testkey',
                 self.now(),
                 'testvalue')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 新节点创建table
        rs3 = self.create(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs3)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs4 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('Fail to LoadTable' in rs4)


    def test_loadtable_can_be_pausedsnapshot_after_loadtable(self):
        """
        loadtable以后，可以正常暂停snapshot
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'testkey',
                 self.now(),
                 'testvalue')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)

        rs4 = self.pausesnapshot(self.slave1, self.tid, self.pid)
        self.assertTrue('PauseSnapshot ok' in rs4)
        table_status = self.get_table_status(self.slave1, self.tid, self.pid)
        self.assertEqual(table_status, ['1', 'kTableFollower', 'kSnapshotPaused', 'true', '144000min', '0s'])


    # @multi_dimension(False)
    def test_loadtable_by_snapshot_and_binlog(self):
        """
        同时通过snapshot和binlog loadtable
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 3):
            # for multidimension test
            self.multidimension_vk = {'card': ('string:index', 'testkey{}'.format(i)),
                                      'merchant': ('string:index', 'testvalue{}'.format(i)),
                                      'amt': ('double', 1.1)}
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey{}'.format(i),
                     self.now() - i,
                     'testvalue{}'.format(i))
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        for i in range(3, 6):
            # for multidimension test
            self.multidimension_vk = {'card': ('string:index', 'testkey{}'.format(i)),
                                      'merchant': ('string:index', 'testvalue{}'.format(i)),
                                      'amt': ('double', 1.1)}
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey{}'.format(i),
                     self.now() - i,
                     'testvalue{}'.format(i))
        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)

        for i in range(0, 6):
            self.multidimension_scan_vk = {'card': 'testkey{}'.format(i)}  # for multidimension test
            rs = self.scan(self.slave1, self.tid, self.pid, 'testkey{}'.format(i), self.now(), 1)
            self.assertTrue('testvalue{}'.format(i) in rs)


    def test_loadtable_by_binlog_success(self):
        """
        仅通过binlog loadtable
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'testkey',
                 self.now() - 10,
                 'testvalue')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)
        # 将table目录拷贝到新节点，删掉snapshot目录，保留binlog目录
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)
        self.exe_shell('rm -rf {}/db/{}_{}/snapshot/*'.format(self.slave1path, self.tid, self.pid))

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)
        self.assertTrue('testvalue' in self.scan(self.slave1, self.tid, self.pid, 'testkey', self.now(), 1))

        rs4 = self.makesnapshot(self.slave1, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs4)
        mf = self.get_manifest(self.slave1path, self.tid, self.pid)
        self.assertEqual(mf['offset'], '1')
        self.assertTrue(mf['name'])
        self.assertEqual(mf['count'], '1')


    def test_loadtable_by_binlog_ttl(self):
        """
        binlog中包含过期数据
        通过binlog loadtable，剔除过期数据
        再makesnapshot可以成功
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 4):
            # for multidimension test
            self.multidimension_vk = {'card': ('string:index', 'testkey'),
                                      'merchant': ('string:index', 'testvalue{}'.format(i)),
                                      'amt': ('double', 1.1)}
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey',
                     self.now() - (100000000000 * (i % 2) + 1),
                     'testvalue{}'.format(i))
        time.sleep(1)
        # 将table目录拷贝到新节点，删掉snapshot目录，保留binlog目录
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)
        self.exe_shell('rm -rf {}/db/{}_{}/snapshot/*'.format(self.slave1path, self.tid, self.pid))

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)
        self.multidimension_scan_vk = {'card': 'testkey'}  # for multidimension test
        self.assertTrue('testvalue0' in self.scan(self.slave1, self.tid, self.pid, 'testkey', self.now(), 1))
        self.assertFalse('testvalue1' in self.scan(self.slave1, self.tid, self.pid, 'testkey', self.now(), 1))

        rs4 = self.makesnapshot(self.slave1, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs4)
        mf = self.get_manifest(self.slave1path, self.tid, self.pid)
        self.assertEqual(mf['offset'], '4')
        self.assertTrue(mf['name'])
        self.assertEqual(mf['count'], '2')


    def test_loadtable_by_binlog_after_makesnapshots(self):
        """
        多次makesnapshot后，可以通过binlog loadtable，且数据完整
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 3):
            # for multidimension test
            self.multidimension_vk = {'card': ('string:index', 'testkey1'),
                                      'merchant': ('string:index', 'testvalue1'),
                                      'amt': ('double', 1.1)}
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey1',
                     self.now() - i,
                     'testvalue1')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        for i in range(0, 3):
            # for multidimension test
            self.multidimension_vk = {'card': ('string:index', 'testkey2'),
                                      'merchant': ('string:index', 'testvalue2'),
                                      'amt': ('double', 1.1)}
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey2',
                     self.now() - i,
                     'testvalue2')

        # 将table目录拷贝到新节点，删掉snapshot目录，保留binlog目录
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)
        self.exe_shell('rm -rf {}/db/{}_{}/snapshot/*'.format(self.slave1path, self.tid, self.pid))

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)

        self.multidimension_scan_vk = {'card': 'testkey1'}  # for multidimension test
        self.assertTrue('testvalue1' in self.scan(self.slave1, self.tid, self.pid, 'testkey1', self.now(), 1))
        self.multidimension_scan_vk = {'card': 'testkey2'}  # for multidimension test
        self.assertTrue('testvalue2' in self.scan(self.slave1, self.tid, self.pid, 'testkey2', self.now(), 1))

        rs4 = self.makesnapshot(self.slave1, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs4)
        mf = self.get_manifest(self.slave1path, self.tid, self.pid)
        self.assertEqual(mf['offset'], '6')
        self.assertTrue(mf['name'])
        self.assertEqual(mf['count'], '6')
        table_status = self.get_table_status(self.leader, self.tid, self.pid)
        self.assertEqual(table_status, ['6', 'kTableLeader', 'kTableNormal', 'true', '144000min', '0s'])


    def test_loadtable_after_recoversnapshot(self):
        """
        recoversnapshot后，拷贝db到新节点，新节点可以loadtable成功，数据完整
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        # for multidimension test
        self.multidimension_vk = {'card': ('string:index', 'testkey1'),
                                  'merchant': ('string:index', 'testvalue1'),
                                  'amt': ('double', 1.1)}
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'testkey1',
                 self.now(),
                 'testvalue1')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        rs3 = self.pausesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('PauseSnapshot ok' in rs3)
        rs5 = self.recoversnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('RecoverSnapshot ok' in rs5)

        # for multidimension test
        self.multidimension_vk = {'card': ('string:index', 'testkey2'),
                                  'merchant': ('string:index', 'testvalue2'),
                                  'amt': ('double', 1.1)}
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'testkey2',
                 self.now(),
                 'testvalue2')
        rs6 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs6)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs7 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs7)

        self.multidimension_scan_vk = {'card': 'testkey1'}  # for multidimension test
        self.assertTrue('testvalue1' in self.scan(self.slave1, self.tid, self.pid, 'testkey1', self.now(), 1))
        self.multidimension_scan_vk = {'card': 'testkey2'}  # for multidimension test
        self.assertTrue('testvalue2' in self.scan(self.slave1, self.tid, self.pid, 'testkey2', self.now(), 1))

        rs8 = self.makesnapshot(self.slave1, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs8)
        mf = self.get_manifest(self.slave1path, self.tid, self.pid)
        self.assertEqual(mf['offset'], '2')
        self.assertTrue(mf['name'])
        self.assertEqual(mf['count'], '2')
        table_status = self.get_table_status(self.leader, self.tid, self.pid)
        self.assertEqual(table_status, ['2', 'kTableLeader', 'kTableNormal', 'true', '144000min', '0s'])


    def test_loadtable_manitest_deleted(self):
        """
        MANIFEST文件被删除，loadtable时无法load数据，log中有warning
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'testkey',
                 self.now() - 10,
                 'testvalue')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点，并删掉manifest和binlog
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)
        self.exe_shell('rm -f {}/db/{}_{}/snapshot/MANIFEST'.format(self.slave1path, self.tid, self.pid))
        self.exe_shell('rm -rf {}/db/{}_{}/binlog'.format(self.slave1path, self.tid, self.pid))

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)

        rs4 = self.makesnapshot(self.slave1, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs4)
        mf = self.get_manifest(self.slave1path, self.tid, self.pid)
        self.assertEqual(mf['offset'], '0')
        self.assertTrue(mf['name'])
        self.assertEqual(mf['count'], '0')


    def test_loadtable_snapshot_deleted(self):
        """
        snapshot文件被删除，loadtable时无法load数据，log中有warning
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'testkey',
                 self.now(),
                 'testvalue')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点，并删掉sdb和binlog
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)
        self.exe_shell('rm -f {}/db/{}_{}/snapshot/*.sdb'.format(self.slave1path, self.tid, self.pid))
        self.exe_shell('rm -rf {}/db/{}_{}/binlog'.format(self.slave1path, self.tid, self.pid))

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)
        mf = self.get_manifest(self.slave1path, self.tid, self.pid)
        self.assertEqual(mf['offset'], '1')
        self.assertTrue(mf['name'])
        self.assertEqual(mf['count'], '1')


    def test_loadtable_snapshot_name_mismatch(self):
        """
        MANIFEST和snapshot文件名不匹配，loadtable时无法load数据，log中有warning
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        self.put(self.leader,
                 self.tid,
                 self.pid,
                 'testkey',
                 self.now(),
                 'testvalue')
        rs2 = self.makesnapshot(self.leader, self.tid, self.pid)
        self.assertTrue('MakeSnapshot ok' in rs2)

        # 将table目录拷贝到新节点，删除binlog，重命名sdb
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)
        self.exe_shell('rm -rf {}/db/{}_{}/binlog'.format(self.slave1path, self.tid, self.pid))
        self.exe_shell('mv {nodepath}/db/{tid}_{pid}/snapshot/*.sdb \
            {nodepath}/db/{tid}_{pid}/snapshot/11111.sdb'.format(
                nodepath=self.slave1path, tid=self.tid, pid=self.pid))

        rs3 = self.loadtable(self.slave1, 't', self.tid, self.pid)
        self.assertTrue('LoadTable ok' in rs3)


    def test_loadtable_fail_when_loading(self):
        """
        loadtable过程中不允许再次loadtable
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)

        self.put_large_datas(500, 10)

        # 将table目录拷贝到新节点
        self.cp_db(self.leaderpath, self.slave1path, self.tid, self.pid)

        rs_list = []

        def loadtable(endpoint):
            rs = self.loadtable(endpoint, 't', self.tid, self.pid)
            rs_list.append(rs)

        # 5个线程并发loadtable，最后只有1个线程是load ok的
        threads = []
        for _ in range(0, 5):
            threads.append(threading.Thread(
                target=loadtable, args=(self.slave1,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print rs_list
        self.assertEqual(rs_list.count('LoadTable ok'), 1)


    @multi_dimension(False)
    def test_loadtable_and_addreplica_ttl(self):
        """
        主节点将从节点添加为副本，没有snapshot和binlog
        从节点loadtable，可以正确load到未过期的数据
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 6):
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     'testkey',
                     self.now() - (100000000000 * (i % 2) + 1),
                     'testvalue{}'.format(i))
        rs1 = self.loadtable(self.slave1, 't', self.tid, self.pid, 144000, 8, 'false', self.slave1)
        self.assertTrue('Fail' in rs1)
        rs0 = self.create(self.slave1, 't', self.tid, self.pid, 144000, 8, 'false', self.slave1)
        self.assertTrue('Create table ok' in rs0)
        rs2 = self.addreplica(self.leader, self.tid, self.pid, 'client', self.slave1)
        self.assertTrue('AddReplica ok' in rs2)
        time.sleep(1)
        self.assertTrue('testvalue0' in self.scan(self.slave1, self.tid, self.pid, 'testkey', self.now(), 1))
        self.assertTrue('testvalue1' in self.scan(self.slave1, self.tid, self.pid, 'testkey', self.now(), 1))
        time.sleep(60)
        self.assertTrue('testvalue0' in self.scan(self.slave1, self.tid, self.pid, 'testkey', self.now(), 1))
        self.assertFalse('testvalue1' in self.scan(self.slave1, self.tid, self.pid, 'testkey', self.now(), 1))


    @multi_dimension(True)
    def test_loadtable_and_addreplica_ttl_md(self):
        """
        主节点将从节点添加为副本，没有snapshot和binlog
        从节点loadtable，可以正确load到未过期的数据
        :return:
        """
        rs1 = self.create(self.leader, 't', self.tid, self.pid)
        self.assertTrue('Create table ok' in rs1)
        for i in range(0, 6):
            self.put(self.leader,
                     self.tid,
                     self.pid,
                     '',
                     self.now() - (100000000000 * (i % 2) + 1),
                     'testvalue{}'.format(i), '1.1', 'testkey')
        rs1 = self.loadtable(self.slave1, 't', self.tid, self.pid, 144000, 8, 'false')
        self.assertTrue('Fail' in rs1)
        rs0 = self.create(self.slave1, 't', self.tid, self.pid, 144000, 8, 'false')
        self.assertTrue('Create table ok' in rs0)
        rs2 = self.addreplica(self.leader, self.tid, self.pid, 'client', self.slave1)
        self.assertTrue('AddReplica ok' in rs2)
        time.sleep(1)
        self.assertTrue('testvalue0' in self.scan(
            self.slave1, self.tid, self.pid, {'card': 'testkey'}, self.now(), 1))
        self.assertTrue('testvalue1' in self.scan(
            self.slave1, self.tid, self.pid, {'card': 'testkey'}, self.now(), 1))
        time.sleep(60)
        self.assertTrue('testvalue0' in self.scan(
            self.slave1, self.tid, self.pid, {'card': 'testkey'}, self.now(), 1))
        self.assertFalse('testvalue1' in self.scan(
            self.slave1, self.tid, self.pid, {'card': 'testkey'}, self.now(), 1))

   
if __name__ == "__main__":
    load(TestLoadTable)
