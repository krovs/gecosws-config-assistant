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


import os
import shlex
import subprocess
from gi.repository import Gtk
from firstboot_lib import PageWindow
from firstboot import serverconf
import firstboot.validation as validation

import gettext
from gettext import gettext as _
gettext.textdomain('firstboot')

import firstboot.pages


__REQUIRED__ = False

__TITLE__ = _('Date/Time Synchronization')


def get_page(main_window):

    page = DateSyncPage(main_window)
    return page


class DateSyncPage(PageWindow.PageWindow):
    __gtype_name__ = "DateSyncPage"

    def finish_initializing(self):
        self.set_status(None)

    def load_page(self, params=None):
        self.emit('status-changed', 'dateSync', not __REQUIRED__)

        self.serverconf = serverconf.get_server_conf(None)
        if serverconf.json_is_cached():
            self.ui.txtHost.set_text(self.serverconf.get_ntp_conf().get_host())

    def translate(self):
        desc = _('Workstations and server time must be synchronized.\nPlease,\
 provide the name or IP address of a valid Network Time Protocol server.')

        self.ui.lblDescription.set_text(desc)
        self.ui.lblHost.set_label(_('NTP Server'))
        #self.ui.btnSync.set_label(_('Synchronize'))

    def on_btnSync_clicked(self, widget):
        pass
        """
        self.ui.btnSync.set_sensitive(False)
        cmd = 'ntpdate -u %s' % (self.ui.txtHost.get_text(),)
        args = shlex.split(cmd)

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #exit_code = os.waitpid(process.pid, 0)
        exit_code = process.wait()
        output = process.communicate()
        output = "%s%s" % (output[0].strip(), output[1].strip())

        self.ui.btnSync.set_sensitive(True)
        self.set_status(exit_code, output)
        """

    def set_status(self, code, description=''):

        self.ui.imgStatus.set_visible(code != None)
        self.ui.lblStatus.set_visible(code != None)

        if code == None:
            return

        if code == 0:
            icon = Gtk.STOCK_YES

        else:
            icon = Gtk.STOCK_DIALOG_ERROR

        self.ui.imgStatus.set_from_stock(icon, Gtk.IconSize.MENU)
        self.ui.lblStatus.set_label(description)

    def previous_page(self, load_page_callback):
        load_page_callback(firstboot.pages.network)

    def next_page(self, load_page_callback):
        if validation.is_domain(self.ui.txtHost.get_text()):
            self.serverconf.get_ntp_conf().set_uri_ntp(self.ui.txtHost.get_text())
            #print self.serverconf.get_ntp_conf().get_uri_ntp()
            load_page_callback(firstboot.pages.linkToChef)
        else:
            raise Exception(_('Incorrect value for NTP Server'))
        
        
