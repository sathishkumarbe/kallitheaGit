# -*- coding: utf-8 -*-
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
kallithea.controllers.forks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

forks controller for Kallithea

This file was forked by the Kallithea project in July 2014.
Original author and date, and relevant copyright and licensing information is below:
:created_on: Apr 23, 2011
:author: marcink
:copyright: (c) 2013 RhodeCode GmbH, and others.
:license: GPLv3, see LICENSE.md for more details.
"""

import logging
import formencode
import traceback
from formencode import htmlfill

from pylons import tmpl_context as c, request, url
from pylons.i18n.translation import _
from webob.exc import HTTPFound

import kallithea.lib.helpers as h

from kallithea.lib.helpers import Page
from kallithea.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator, \
    NotAnonymous, HasRepoPermissionAny, HasPermissionAnyDecorator, HasPermissionAny
from kallithea.lib.base import BaseRepoController, render
from kallithea.model.db import Repository, UserFollowing, User, Ui
from kallithea.model.repo import RepoModel
from kallithea.model.forms import RepoForkForm
from kallithea.model.scm import ScmModel, AvailableRepoGroupChoices
from kallithea.lib.utils2 import safe_int

log = logging.getLogger(__name__)


class ForksController(BaseRepoController):

    def __before__(self):
        super(ForksController, self).__before__()

    def __load_defaults(self):
        repo_group_perms = ['group.admin']
        if HasPermissionAny('hg.create.write_on_repogroup.true')():
            repo_group_perms.append('group.write')
        c.repo_groups = AvailableRepoGroupChoices(['hg.create.repository'], repo_group_perms)

        c.landing_revs_choices, c.landing_revs = ScmModel().get_repo_landing_revs()

        c.can_update = Ui.get_by_key('hooks', Ui.HOOK_UPDATE).ui_active

    def __load_data(self, repo_name=None):
        """
        Load defaults settings for edit, and update

        :param repo_name:
        """
        self.__load_defaults()

        c.repo_info = db_repo = Repository.get_by_repo_name(repo_name)
        repo = db_repo.scm_instance

        if c.repo_info is None:
            h.not_mapped_error(repo_name)
            raise HTTPFound(location=url('repos'))

        c.default_user_id = User.get_default_user().user_id
        c.in_public_journal = UserFollowing.query() \
            .filter(UserFollowing.user_id == c.default_user_id) \
            .filter(UserFollowing.follows_repository == c.repo_info).scalar()

        if c.repo_info.stats:
            last_rev = c.repo_info.stats.stat_on_revision+1
        else:
            last_rev = 0
        c.stats_revision = last_rev

        c.repo_last_rev = repo.count() if repo.revisions else 0

        if last_rev == 0 or c.repo_last_rev == 0:
            c.stats_percentage = 0
        else:
            c.stats_percentage = '%.2f' % ((float((last_rev)) /
                                            c.repo_last_rev) * 100)

        defaults = RepoModel()._get_defaults(repo_name)
        # alter the description to indicate a fork
        defaults['description'] = ('fork of repository: %s \n%s'
                                   % (defaults['repo_name'],
                                      defaults['description']))
        # add suffix to fork
        defaults['repo_name'] = '%s-fork' % defaults['repo_name']

        return defaults

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def forks(self, repo_name):
        p = safe_int(request.GET.get('page', 1), 1)
        repo_id = c.db_repo.repo_id
        d = []
        for r in Repository.get_repo_forks(repo_id):
            if not HasRepoPermissionAny(
                'repository.read', 'repository.write', 'repository.admin'
            )(r.repo_name, 'get forks check'):
                continue
            d.append(r)
        c.forks_pager = Page(d, page=p, items_per_page=20)

        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            return render('/forks/forks_data.html')

        return render('/forks/forks.html')

    @LoginRequired()
    @NotAnonymous()
    @HasPermissionAnyDecorator('hg.admin', 'hg.fork.repository')
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def fork(self, repo_name):
        c.repo_info = Repository.get_by_repo_name(repo_name)
        if not c.repo_info:
            h.not_mapped_error(repo_name)
            raise HTTPFound(location=url('home'))

        defaults = self.__load_data(repo_name)

        return htmlfill.render(
            render('forks/fork.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False)

    @LoginRequired()
    @NotAnonymous()
    @HasPermissionAnyDecorator('hg.admin', 'hg.fork.repository')
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def fork_create(self, repo_name):
        self.__load_defaults()
        c.repo_info = Repository.get_by_repo_name(repo_name)
        _form = RepoForkForm(old_data={'repo_type': c.repo_info.repo_type},
                             repo_groups=c.repo_groups,
                             landing_revs=c.landing_revs_choices)()
        form_result = {}
        task_id = None
        try:
            form_result = _form.to_python(dict(request.POST))

            # an approximation that is better than nothing
            if not Ui.get_by_key('hooks', Ui.HOOK_UPDATE).ui_active:
                form_result['update_after_clone'] = False

            # create fork is done sometimes async on celery, db transaction
            # management is handled there.
            task = RepoModel().create_fork(form_result, self.authuser.user_id)
            from celery.result import BaseAsyncResult
            if isinstance(task, BaseAsyncResult):
                task_id = task.task_id
        except formencode.Invalid as errors:
            return htmlfill.render(
                render('forks/fork.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False)
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during repository forking %s') %
                    repo_name, category='error')

        raise HTTPFound(location=h.url('repo_creating_home',
                              repo_name=form_result['repo_name_full'],
                              task_id=task_id))
