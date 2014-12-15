from __future__ import with_statement
from kallithea.tests import *
from kallithea.lib.diffs import DiffProcessor, NEW_FILENODE, DEL_FILENODE, \
    MOD_FILENODE, RENAMED_FILENODE, CHMOD_FILENODE, BIN_FILENODE, COPIED_FILENODE
from kallithea.tests.fixture import Fixture

fixture = Fixture()


DIFF_FIXTURES = {
    'hg_diff_add_single_binary_file.diff': [
        ('US Warszawa.jpg', 'A',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {NEW_FILENODE: 'new file 100755',
                  BIN_FILENODE: 'binary diff not shown'}}),
    ],
    'hg_diff_mod_single_binary_file.diff': [
        ('US Warszawa.jpg', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {MOD_FILENODE: 'modified file',
                  BIN_FILENODE: 'binary diff not shown'}}),
    ],

    'hg_diff_mod_single_file_and_rename_and_chmod.diff': [
        ('README', 'R',
         {'added': 3,
          'deleted': 0,
          'binary': False,
          'ops': {RENAMED_FILENODE: 'file renamed from README.rst to README',
                  CHMOD_FILENODE: 'modified file chmod 100755 => 100644'}}),
    ],
    'hg_diff_mod_file_and_rename.diff': [
        ('README.rst', 'R',
         {'added': 3,
          'deleted': 0,
          'binary': False,
          'ops': {RENAMED_FILENODE: 'file renamed from README to README.rst'}}),
    ],
    'hg_diff_del_single_binary_file.diff': [
        ('US Warszawa.jpg', 'D',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {DEL_FILENODE: 'deleted file',
                  BIN_FILENODE: 'binary diff not shown'}}),
    ],
    'hg_diff_chmod_and_mod_single_binary_file.diff': [
        ('gravatar.png', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {CHMOD_FILENODE: 'modified file chmod 100644 => 100755',
                  BIN_FILENODE: 'binary diff not shown'}}),
    ],
    'hg_diff_chmod.diff': [
        ('file', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {CHMOD_FILENODE: 'modified file chmod 100755 => 100644'}}),
    ],
    'hg_diff_rename_file.diff': [
        ('file_renamed', 'R',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {RENAMED_FILENODE: 'file renamed from file to file_renamed'}}),
    ],
    'hg_diff_rename_and_chmod_file.diff': [
        ('README', 'R',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {CHMOD_FILENODE: 'modified file chmod 100644 => 100755',
                  RENAMED_FILENODE: 'file renamed from README.rst to README'}}),
    ],
    'hg_diff_binary_and_normal.diff': [
        ('img/baseline-10px.png', 'A',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {NEW_FILENODE: 'new file 100644',
                  BIN_FILENODE: 'binary diff not shown'}}),
        ('img/baseline-20px.png', 'D',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {DEL_FILENODE: 'deleted file',
                  BIN_FILENODE: 'binary diff not shown'}}),
        ('index.html', 'M',
         {'added': 3,
          'deleted': 2,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('js/global.js', 'D',
         {'added': 0,
          'deleted': 75,
          'binary': False,
          'ops': {DEL_FILENODE: 'deleted file'}}),
        ('js/jquery/hashgrid.js', 'A',
         {'added': 340,
          'deleted': 0,
          'binary': False,
          'ops': {NEW_FILENODE: 'new file 100755'}}),
        ('less/docs.less', 'M',
         {'added': 34,
          'deleted': 0,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('less/scaffolding.less', 'M',
         {'added': 1,
          'deleted': 3,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('readme.markdown', 'M',
         {'added': 1,
          'deleted': 10,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
    ],
    'git_diff_chmod.diff': [
        ('work-horus.xls', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {CHMOD_FILENODE: 'modified file chmod 100644 => 100755'}})
    ],
    'git_diff_rename_file.diff': [
        ('file.xls', 'R',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {RENAMED_FILENODE: 'file renamed from work-horus.xls to file.xls'}})
    ],
    'git_diff_mod_single_binary_file.diff': [
        ('US Warszawa.jpg', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {MOD_FILENODE: 'modified file',
                  BIN_FILENODE: 'binary diff not shown'}})
    ],
    'git_diff_binary_and_normal.diff': [
        ('img/baseline-10px.png', 'A',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {NEW_FILENODE: 'new file 100644',
                  BIN_FILENODE: 'binary diff not shown'}}),
        ('img/baseline-20px.png', 'D',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {DEL_FILENODE: 'deleted file',
                  BIN_FILENODE: 'binary diff not shown'}}),
        ('index.html', 'M',
         {'added': 3,
          'deleted': 2,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('js/global.js', 'D',
         {'added': 0,
          'deleted': 75,
          'binary': False,
          'ops': {DEL_FILENODE: 'deleted file'}}),
        ('js/jquery/hashgrid.js', 'A',
         {'added': 340,
          'deleted': 0,
          'binary': False,
          'ops': {NEW_FILENODE: 'new file 100755'}}),
        ('less/docs.less', 'M',
         {'added': 34,
          'deleted': 0,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('less/scaffolding.less', 'M',
         {'added': 1,
          'deleted': 3,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('readme.markdown', 'M',
         {'added': 1,
          'deleted': 10,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
    ],
    'diff_with_diff_data.diff': [
        ('vcs/backends/base.py', 'M',
         {'added': 18,
          'deleted': 2,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('vcs/backends/git/repository.py', 'M',
         {'added': 46,
          'deleted': 15,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('vcs/backends/hg.py', 'M',
         {'added': 22,
          'deleted': 3,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('vcs/tests/test_git.py', 'M',
         {'added': 5,
          'deleted': 5,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
        ('vcs/tests/test_repository.py', 'M',
         {'added': 174,
          'deleted': 2,
          'binary': False,
          'ops': {MOD_FILENODE: 'modified file'}}),
    ],
    'hg_diff_copy_file.diff': [
        ('file2', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {COPIED_FILENODE: 'file copied from file1 to file2'}}),
    ],
    'hg_diff_copy_and_modify_file.diff': [
        ('file3', 'M',
         {'added': 1,
          'deleted': 0,
          'binary': False,
          'ops': {COPIED_FILENODE: 'file copied from file2 to file3',
                  MOD_FILENODE: 'modified file'}}),
    ],
    'hg_diff_copy_and_chmod_file.diff': [
        ('file4', 'M',
         {'added': 0,
          'deleted': 0,
          'binary': True,
          'ops': {COPIED_FILENODE: 'file copied from file3 to file4',
                  CHMOD_FILENODE: 'modified file chmod 100644 => 100755'}}),
    ],
    'hg_diff_copy_chmod_and_edit_file.diff': [
        ('file5', 'M',
         {'added': 2,
          'deleted': 1,
          'binary': False,
          'ops': {COPIED_FILENODE: 'file copied from file4 to file5',
                  CHMOD_FILENODE: 'modified file chmod 100755 => 100644',
                  MOD_FILENODE: 'modified file'}}),
    ],
    'hg_diff_rename_space_cr.diff': [
        ('ohyes', 'R',
         {'added': 4,
          'deleted': 2,
          'binary': False,
          'ops': {RENAMED_FILENODE: 'file renamed from ohno to ohyes'}}),
    ],
}


class DiffLibTest(BaseTestCase):

    @parameterized.expand([(x,) for x in DIFF_FIXTURES])
    def test_diff(self, diff_fixture):

        diff = fixture.load_resource(diff_fixture, strip=False)

        diff_proc = DiffProcessor(diff)
        diff_proc_d = diff_proc.prepare()
        data = [(x['filename'], x['operation'], x['stats']) for x in diff_proc_d]
        expected_data = DIFF_FIXTURES[diff_fixture]
        self.assertListEqual(expected_data, data)
