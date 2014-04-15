# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

# This file is part of Guadalinex
#
# This software is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this package; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

__author__ = "Antonio Hernández <ahernandez@emergya.com>"
__copyright__ = "Copyright (C) 2011, Junta de Andalucía <devmaster@guadalinex.org>"
__license__ = "GPL-2"


import LinkToChefHostnamePage
import LinkToChefResultsPage
import firstboot.pages.linkToChef
from firstboot.pages.network import interface
from firstboot_lib import PageWindow
from firstboot import serverconf
import firstboot.validation as validation

from gi.repository import Gtk
import requests
import hashlib
import gettext
from gettext import gettext as _
gettext.textdomain('firstboot')

__REQUIRED__ = False

__STATUS_TEST_PASSED__ = 0
__STATUS_CONFIG_CHANGED__ = 1
__STATUS_CONNECTING__ = 2
__STATUS_ERROR__ = 3


def get_page(main_window):

    page = LinkToChefConfEditorPage(main_window)
    return page


class LinkToChefConfEditorPage(PageWindow.PageWindow):
    __gtype_name__ = "LinkToChefConfEditorPage"

    def finish_initializing(self):
        self.show_status()

    def load_page(self, params=None):
        #content = serverconf.get_json_content()
        self.serverconf = serverconf.get_server_conf(None)
        self.gcc_conf = self.serverconf.get_gcc_conf()
        self.chef_conf = self.serverconf.get_chef_conf()
        self.ui.txtUrlChef.set_text(self.gcc_conf.get_uri_gcc())
        self.ui.txtUser.set_text(self.gcc_conf.get_gcc_username())

    def translate(self):
        desc = _('These parameters are required in order to join a Control Center:')

        self.ui.lblDescription.set_text(desc)
        self.ui.lblUrlChefDesc.set_label(_('"Control Center URL": an existant URL in your server where GECOS Control Center is installed.'))
        self.ui.lblUsernameDesc.set_label(_('"Username": User with administrative privilees (This will not be workstation user)'))
        self.ui.lblUrlChef.set_label('Control Center URL')
        self.ui.lblUser.set_label(_('Control Center Username'))
        self.ui.lblPassword.set_label(_('Password'))

    def previous_page(self, load_page_callback):
        load_page_callback(firstboot.pages.linkToChef)

    def next_page(self, load_page_callback):
        self.gcc_conf.set_uri_gcc(self.ui.txtUrlChef.get_text())
        self.gcc_conf.set_gcc_username(self.ui.txtUser.get_text())
        self.gcc_conf.set_gcc_pwd_user(self.ui.txtPassword.get_text())
        self.gcc_conf.set_gcc_link(True)
        self.interfaces = interface.localifs()
        self.interfaces.reverse()
        for inter in self.interfaces:
            if not inter[1].startswith('127.0'):
                break
        if not serverconf.json_is_cached():
            result = serverconf.url_chef(_('Url Chef Certificate Required'), _('You need to enter url with certificate file\n in protocol://domain/resource format'))
            try:
                req = requests.get(result)
                if not req.ok:
                    raise LinkToChefException(_("Can not download pem file"))
                pem = req.text
                self.chef_conf.set_pem(pem)
                self.chef_conf.set_url(self.gcc_conf.get_uri_gcc())

            except Exception as e:
                self.show_status(__STATUS_ERROR__, e)
        mac = interface.getHwAddr(inter[0])
        node_name = hashlib.md5(mac.encode()).hexdigest()
        self.gcc_conf.set_gcc_nodename(node_name)
        result, messages = self.validate_conf()
        load_page_callback(LinkToChefResultsPage, {
            'result': result,
            'messages': messages
         })

        
#        if not self.unlink_from_chef:
#
#            result, messages = self.validate_conf()
#
#            if result == True:
#                result, messages = serverconf.setup_server(
#                    server_conf=self.server_conf,
#                    link_ldap=False,
#                    unlink_ldap=False,
#                    link_chef=not self.unlink_from_chef,
#                    unlink_chef=self.unlink_from_chef
#                )
#
#            load_page_callback(LinkToChefResultsPage, {
#                'server_conf': self.server_conf,
#                'result': result,
#                'messages': messages
#            })
#
#        else:
#            result, messages = serverconf.setup_server(
#                server_conf=self.server_conf,
#                link_chef=not self.unlink_from_chef,
#                unlink_chef=self.unlink_from_chef
#            )
#
#            load_page_callback(LinkToChefResultsPage, {
#                'result': result,
#                'server_conf': self.server_conf,
#                'messages': messages
#            })

    def on_serverConf_changed(self, entry):
        if not self.update_server_conf:
            return
        self.server_conf.get_chef_conf().set_url(self.ui.txtUrlChef.get_text())
   #     self.server_conf.get_chef_conf().set_pem_url(self.ui.txtUrlChefCert.get_text())
   #     self.server_conf.get_chef_conf().set_default_role(self.ui.txtDefaultRole.get_text())
        self.server_conf.get_chef_conf().set_hostname(self.ui.txtHostname.get_text())

    def validate_conf(self):

        valid = True
        messages = []

        if not self.server_conf.get_chef_conf().validate():
            valid = False
            messages.append({'type': 'error', 'message': _('Chef and Chef Cert URLs must be valid URLs.')})

        hostname = self.server_conf.get_chef_conf().get_hostname()

        if not validation.is_qname(hostname):
            valid = False
            messages.append({'type': 'error', 'message': _('Node name is empty or contains invalid characters.')})

        try:
            used_hostnames = serverconf.get_chef_hostnames(self.server_conf.get_chef_conf())

        except Exception as e:
            used_hostnames = []
            # IMPORTANT: Append the error but don't touch the variable "valid" here,
            # just because if we can't get the hostnames here,
            # Chef will inform us about that later, while we are registering
            # the client.
            messages.append({'type': 'error', 'message': str(e)})

        if hostname in used_hostnames:
            valid = False
            messages.append({'type': 'error', 'message': _('Node name already exists in the Chef server. Choose a different one.')})

        return valid, messages
