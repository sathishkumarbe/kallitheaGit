import os
import unittest
from rhodecode.tests import *

from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.db import RepoGroup, User, Notification, UserNotification, \
    UsersGroup, UsersGroupMember
from sqlalchemy.exc import IntegrityError
from rhodecode.model.user import UserModel

from rhodecode.model.meta import Session
from rhodecode.model.notification import NotificationModel
from rhodecode.model.users_group import UsersGroupModel

class TestReposGroups(unittest.TestCase):

    def setUp(self):
        self.g1 = self.__make_group('test1', skip_if_exists=True)
        self.g2 = self.__make_group('test2', skip_if_exists=True)
        self.g3 = self.__make_group('test3', skip_if_exists=True)

    def tearDown(self):
        print 'out'

    def __check_path(self, *path):
        path = [TESTS_TMP_PATH] + list(path)
        path = os.path.join(*path)
        return os.path.isdir(path)

    def _check_folders(self):
        print os.listdir(TESTS_TMP_PATH)

    def __make_group(self, path, desc='desc', parent_id=None,
                     skip_if_exists=False):

        gr = RepoGroup.get_by_group_name(path)
        if gr and skip_if_exists:
            return gr

        form_data = dict(group_name=path,
                         group_description=desc,
                         group_parent_id=parent_id)
        gr = ReposGroupModel().create(form_data)
        Session.commit()
        return gr

    def __delete_group(self, id_):
        ReposGroupModel().delete(id_)


    def __update_group(self, id_, path, desc='desc', parent_id=None):
        form_data = dict(group_name=path,
                         group_description=desc,
                         group_parent_id=parent_id)

        gr = ReposGroupModel().update(id_, form_data)
        return gr

    def test_create_group(self):
        g = self.__make_group('newGroup')
        self.assertEqual(g.full_path, 'newGroup')

        self.assertTrue(self.__check_path('newGroup'))


    def test_create_same_name_group(self):
        self.assertRaises(IntegrityError, lambda:self.__make_group('newGroup'))
        Session.rollback()

    def test_same_subgroup(self):
        sg1 = self.__make_group('sub1', parent_id=self.g1.group_id)
        self.assertEqual(sg1.parent_group, self.g1)
        self.assertEqual(sg1.full_path, 'test1/sub1')
        self.assertTrue(self.__check_path('test1', 'sub1'))

        ssg1 = self.__make_group('subsub1', parent_id=sg1.group_id)
        self.assertEqual(ssg1.parent_group, sg1)
        self.assertEqual(ssg1.full_path, 'test1/sub1/subsub1')
        self.assertTrue(self.__check_path('test1', 'sub1', 'subsub1'))


    def test_remove_group(self):
        sg1 = self.__make_group('deleteme')
        self.__delete_group(sg1.group_id)

        self.assertEqual(RepoGroup.get(sg1.group_id), None)
        self.assertFalse(self.__check_path('deteteme'))

        sg1 = self.__make_group('deleteme', parent_id=self.g1.group_id)
        self.__delete_group(sg1.group_id)

        self.assertEqual(RepoGroup.get(sg1.group_id), None)
        self.assertFalse(self.__check_path('test1', 'deteteme'))


    def test_rename_single_group(self):
        sg1 = self.__make_group('initial')

        new_sg1 = self.__update_group(sg1.group_id, 'after')
        self.assertTrue(self.__check_path('after'))
        self.assertEqual(RepoGroup.get_by_group_name('initial'), None)


    def test_update_group_parent(self):

        sg1 = self.__make_group('initial', parent_id=self.g1.group_id)

        new_sg1 = self.__update_group(sg1.group_id, 'after', parent_id=self.g1.group_id)
        self.assertTrue(self.__check_path('test1', 'after'))
        self.assertEqual(RepoGroup.get_by_group_name('test1/initial'), None)


        new_sg1 = self.__update_group(sg1.group_id, 'after', parent_id=self.g3.group_id)
        self.assertTrue(self.__check_path('test3', 'after'))
        self.assertEqual(RepoGroup.get_by_group_name('test3/initial'), None)


        new_sg1 = self.__update_group(sg1.group_id, 'hello')
        self.assertTrue(self.__check_path('hello'))

        self.assertEqual(RepoGroup.get_by_group_name('hello'), new_sg1)



    def test_subgrouping_with_repo(self):

        g1 = self.__make_group('g1')
        g2 = self.__make_group('g2')

        # create new repo
        form_data = dict(repo_name='john',
                         repo_name_full='john',
                         fork_name=None,
                         description=None,
                         repo_group=None,
                         private=False,
                         repo_type='hg',
                         clone_uri=None)
        cur_user = User.get_by_username(TEST_USER_ADMIN_LOGIN)
        r = RepoModel().create(form_data, cur_user)

        self.assertEqual(r.repo_name, 'john')

        # put repo into group
        form_data = form_data
        form_data['repo_group'] = g1.group_id
        form_data['perms_new'] = []
        form_data['perms_updates'] = []
        RepoModel().update(r.repo_name, form_data)
        self.assertEqual(r.repo_name, 'g1/john')


        self.__update_group(g1.group_id, 'g1', parent_id=g2.group_id)
        self.assertTrue(self.__check_path('g2', 'g1'))

        # test repo
        self.assertEqual(r.repo_name, os.path.join('g2', 'g1', r.just_name))

class TestUser(unittest.TestCase):

    def test_create_and_remove(self):
        usr = UserModel().create_or_update(username=u'test_user', password=u'qweqwe',
                                     email=u'u232@rhodecode.org',
                                     name=u'u1', lastname=u'u1')
        Session.commit()
        self.assertEqual(User.get_by_username(u'test_user'), usr)

        # make users group
        users_group = UsersGroupModel().create('some_example_group')
        Session.commit()

        UsersGroupModel().add_user_to_group(users_group, usr)
        Session.commit()

        self.assertEqual(UsersGroup.get(users_group.users_group_id), users_group)
        self.assertEqual(UsersGroupMember.query().count(), 1)
        UserModel().delete(usr.user_id)
        Session.commit()

        self.assertEqual(UsersGroupMember.query().all(), [])


class TestNotifications(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        self.u1 = UserModel().create_or_update(username=u'u1',
                                        password=u'qweqwe',
                                        email=u'u1@rhodecode.org',
                                        name=u'u1', lastname=u'u1')
        Session.commit()
        self.u1 = self.u1.user_id

        self.u2 = UserModel().create_or_update(username=u'u2',
                                        password=u'qweqwe',
                                        email=u'u2@rhodecode.org',
                                        name=u'u2', lastname=u'u3')
        Session.commit()
        self.u2 = self.u2.user_id

        self.u3 = UserModel().create_or_update(username=u'u3',
                                        password=u'qweqwe',
                                        email=u'u3@rhodecode.org',
                                        name=u'u3', lastname=u'u3')
        Session.commit()
        self.u3 = self.u3.user_id

        super(TestNotifications, self).__init__(methodName=methodName)

    def _clean_notifications(self):
        for n in Notification.query().all():
            Session.delete(n)

        Session.commit()
        self.assertEqual(Notification.query().all(), [])


    def test_create_notification(self):
        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        usrs = [self.u1, self.u2]
        notification = NotificationModel().create(created_by=self.u1,
                                           subject=u'subj', body=u'hi there',
                                           recipients=usrs)
        Session.commit()
        u1 = User.get(self.u1)
        u2 = User.get(self.u2)
        u3 = User.get(self.u3)
        notifications = Notification.query().all()
        self.assertEqual(len(notifications), 1)

        unotification = UserNotification.query()\
            .filter(UserNotification.notification == notification).all()

        self.assertEqual(notifications[0].recipients, [u1, u2])
        self.assertEqual(notification.notification_id,
                         notifications[0].notification_id)
        self.assertEqual(len(unotification), len(usrs))
        self.assertEqual([x.user.user_id for x in unotification], usrs)

        self._clean_notifications()

    def test_user_notifications(self):
        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        notification1 = NotificationModel().create(created_by=self.u1,
                                            subject=u'subj', body=u'hi there1',
                                            recipients=[self.u3])
        Session.commit()
        notification2 = NotificationModel().create(created_by=self.u1,
                                            subject=u'subj', body=u'hi there2',
                                            recipients=[self.u3])
        Session.commit()
        u3 = Session.query(User).get(self.u3)

        self.assertEqual(sorted([x.notification for x in u3.notifications]),
                         sorted([notification2, notification1]))
        self._clean_notifications()

    def test_delete_notifications(self):
        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        notification = NotificationModel().create(created_by=self.u1,
                                           subject=u'title', body=u'hi there3',
                                    recipients=[self.u3, self.u1, self.u2])
        Session.commit()
        notifications = Notification.query().all()
        self.assertTrue(notification in notifications)

        Notification.delete(notification.notification_id)
        Session.commit()

        notifications = Notification.query().all()
        self.assertFalse(notification in notifications)

        un = UserNotification.query().filter(UserNotification.notification
                                             == notification).all()
        self.assertEqual(un, [])

        self._clean_notifications()

    def test_delete_association(self):

        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        notification = NotificationModel().create(created_by=self.u1,
                                           subject=u'title', body=u'hi there3',
                                    recipients=[self.u3, self.u1, self.u2])
        Session.commit()

        unotification = UserNotification.query()\
                            .filter(UserNotification.notification ==
                                    notification)\
                            .filter(UserNotification.user_id == self.u3)\
                            .scalar()

        self.assertEqual(unotification.user_id, self.u3)

        NotificationModel().delete(self.u3,
                                   notification.notification_id)
        Session.commit()

        u3notification = UserNotification.query()\
                            .filter(UserNotification.notification ==
                                    notification)\
                            .filter(UserNotification.user_id == self.u3)\
                            .scalar()

        self.assertEqual(u3notification, None)

        # notification object is still there
        self.assertEqual(Notification.query().all(), [notification])

        #u1 and u2 still have assignments
        u1notification = UserNotification.query()\
                            .filter(UserNotification.notification ==
                                    notification)\
                            .filter(UserNotification.user_id == self.u1)\
                            .scalar()
        self.assertNotEqual(u1notification, None)
        u2notification = UserNotification.query()\
                            .filter(UserNotification.notification ==
                                    notification)\
                            .filter(UserNotification.user_id == self.u2)\
                            .scalar()
        self.assertNotEqual(u2notification, None)

        self._clean_notifications()

    def test_notification_counter(self):
        self._clean_notifications()
        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        NotificationModel().create(created_by=self.u1,
                            subject=u'title', body=u'hi there_delete',
                            recipients=[self.u3, self.u1])
        Session.commit()

        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u1), 1)
        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u2), 0)
        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u3), 1)

        notification = NotificationModel().create(created_by=self.u1,
                                           subject=u'title', body=u'hi there3',
                                    recipients=[self.u3, self.u1, self.u2])
        Session.commit()

        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u1), 2)
        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u2), 1)
        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u3), 2)
        self._clean_notifications()
