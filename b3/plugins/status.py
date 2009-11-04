#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
# 03/11/2009 - 1.3.0 - Bakes
# Combined statusftp and status. Use syntax ftp://user:password@host/path/to/status.xml
# 11/02/2009 - 1.2.7 - xlr8or
# If masked show masked level instead of real level
# 11/02/2009 - 1.2.6 - xlr8or
# Sanitized xml data, cleaning ascii < 32 and > 126 (func is in functions.py)
# 21/11/2008 - 1.2.5 - Anubis
# Added PlayerScores
# 12/03/2008 - 1.2.4 - Courgette
# Properly escape strings to ensure valid xml
# 11/30/2005 - 1.2.3 - ThorN
# Use PluginCronTab instead of CronTab
# 8/29/2005 - 1.2.0 - ThorN
# Converted to use new event handlers

__author__  = 'ThorN'
__version__ = '1.3.0'

import b3, time, os, StringIO
import b3.plugin
import b3.cron
from cgi import escape
from ftplib import FTP
from b3 import functions

#--------------------------------------------------------------------------------------------------
class StatusPlugin(b3.plugin.Plugin):
  _tkPlugin = None
  _cronTab = None
  _ftpstatus = False
  _ftpinfo = None
  def onLoadConfig(self):
    if self.config.get('settings','output_file')[0:6] == 'ftp://':
        self._ftpinfo = functions.splitDSN(self.config.get('settings','output_file'))
        self._ftpstatus = True
    else:    
        self._outputFile = os.path.expanduser(self.config.get('settings', 'output_file'))
        
    self._tkPlugin = self.console.getPlugin('tk')
    self._interval = self.config.getint('settings', 'interval')

    if self._cronTab:
      # remove existing crontab
      self.console.cron - self._cronTab

    self._cronTab = b3.cron.PluginCronTab(self, self.update, '*/%s' % self._interval)
    self.console.cron + self._cronTab

  def onEvent(self, event):
    pass

  def update(self):
    clients = self.console.clients.getList()  
    
    scoreList = self.console.getPlayerScores() 
         
    self.verbose('Building XML status')
    xml = '<B3Status Time="%s">\n<Clients Total="%s">\n' % (time.asctime(), len(clients))
        
    for c in clients:
      if not c.name:
        c.name = "@"+str(c.id)
      if c.exactName == "^7":
        c.exactName = "@"+str(c.id)+"^7"

      if not c.maskedLevel:
        _level = c.maxLevel
      else:
        _level = c.maskedLevel

      try:          
        xml += '<Client Name="%s" ColorName="%s" DBID="%s" Connections="%s" CID="%s" Level="%s" GUID="%s" PBID="%s" IP="%s" Team="%s" Joined="%s" Updated="%s" Score="%s" State="%s">\n' % (escape("%s"%sanitizeMe(c.name)), escape("%s"%sanitizeMe(c.exactName)), c.id, c.connections, c.cid, _level, c.guid, c.pbid, c.ip, escape("%s"%c.team), time.ctime(c.timeAdd), time.ctime(c.timeEdit) , scoreList[c.cid], c.state )
        for k,v in c.data.iteritems():
          xml += '<Data Name="%s" Value="%s"/>' % (escape("%s"%k), escape("%s"%sanitizeMe(v))) 
            
        if self._tkPlugin:
          if hasattr(c, 'tkplugin_points'):       
            xml += '<TkPlugin Points="%s">\n' % c.var(self, 'points').toInt()
            if hasattr(c, 'tkplugin_attackers'):
              for acid,points in c.var(self, 'attackers').value.items():
                try:
                  xml += '<Attacker Name="%s" CID="%s" Points="%s"/>\n' % (self.console.clients[acid].name, acid, points)
                except:
                  pass
                
            xml += '</TkPlugin>\n'
        
        xml += '</Client>\n'
      except:
        pass

    c = self.console.game
    xml += '</Clients>\n<Game Name="%s" Type="%s" Map="%s" TimeLimit="%s" FragLimit="%s" CaptureLimit="%s" Rounds="%s">\n' % (escape("%s"%c.gameName), escape("%s"%c.gameType), escape("%s"%c.mapName), c.timeLimit, c.fragLimit, c.captureLimit, c.rounds)
    for k,v in self.console.game.__dict__.items():
      xml += '<Data Name="%s" Value="%s"/>\n' % (escape("%s"%k), escape("%s"%v)) 
    xml += '</Game>\n</B3Status>'
        

    self.writeXML(xml)

  def writeXML(self, xml):
    if self._ftpstatus == True:
      self.debug('Uploading XML status to FTP server')
      ftp=FTP(self._ftpinfo['host'],self._ftpinfo['user'],passwd=self._ftpinfo['password'])
      ftp.cwd(os.path.dirname(self._ftpinfo['path']))
      ftpfile = StringIO.StringIO()
      ftpfile.write(xml)
      ftpfile.seek(0)
      ftp.storlines('STOR '+os.path.basename(self._ftpinfo['path']), ftpfile)
    else:
      self.debug('Writing XML status to %s', self._outputFile)
      f = file(self._outputFile, 'w')
      f.write(xml)
      f.close()