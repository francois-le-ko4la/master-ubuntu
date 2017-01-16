#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This script is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import importlib
from importlib import util
import os
import os.path
import apt
import sys
import socket
import platform
import time
import shutil
import re
import subprocess
from subprocess import Popen, PIPE
import getopt
import locale
import logging
import simplejson as json

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gio

#from dialog import Dialog => menu

"""
----------------------------------------------------------------------------
 #    #    ##     ####    #####  ######  #####
 ##  ##   #  #   #          #    #       #    #
 # ## #  #    #   ####      #    #####   #    #
 #    #  ######       #     #    #       #####
 #    #  #    #  #    #     #    #       #   #
 #    #  #    #   ####      #    ######  #    #

 #     #
 #     #  #####   #    #  #    #   #####  #    #
 #     #  #    #  #    #  ##   #     #    #    #
 #     #  #####   #    #  # #  #     #    #    #
 #     #  #    #  #    #  #  # #     #    #    #
 #     #  #    #  #    #  #   ##     #    #    #
  #####   #####    ####   #    #     #     ####
----------------------------------------------------------------------------

Objectives : setup a fresh install
needs : internet, root privilege
root:root / rwxr-xr-x

sudo apt-get install python3-dialog

----------------------------------------------------------------------------

"""


"""
############################################################################
#
#                      Usage
#
############################################################################
"""

class masterOptions(object):

	 #    #   ####   #        #   #
	 #    #  #    #  #         # #
	 #    #  #       #          #
	 #    #  #  ###  #          #
	 #    #  #    #  #          #
	  ####    ####   ######     #      but quick
	# ------------------ Init
	def __init__(self,argv):
		import argparse
		self.myProg="sudo "+sys.argv[0]
		self.myDescription='''
This personal script setup a new ubuntu environment :
- update/upgrade
- make a \"virtual drive (TMPFS)\" in order to store apt archives
- disable the swap
- install packages
- setup unity environment

This script has been edited and tested on Ubuntu 16.10 according to my personal
needs.
This script needs python3-dialog. It will be installed automaticaly.

Please, launch this script with SUDO. Dont use \"sudo -i\"

You can use, modify, change, do your coffe,... ON YOUR OWN RISKS !!!
This script is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

'''

		# create the top-level parser
		self.parser = argparse.ArgumentParser(prog=self.myProg,
						 formatter_class=argparse.RawDescriptionHelpFormatter,
						 description=self.myDescription,
						 epilog="Enjoy"
						)
		self.parser.add_argument("-f", "--file", help="Change the default configuration file")
		self.parser.add_argument("-o", "--output", metavar='FILE', help="Change the default log file")


		self.groupCLI = self.parser.add_argument_group('all', 'Command line options')
		self.groupCLI.add_argument("-v", "--verbose", action='store_true', help="increase output verbosity.")

		self.subparsers = self.parser.add_subparsers(help='sub-command help')

		# create the parser for the "all" command
		self.parser_all = self.subparsers.add_parser('all', help='all -h')
		self.parser_all.add_argument("-f", "--file", help="Change the default configuration file")
		self.parser_all.add_argument("-o", "--output", metavar='FILE', help="Change the default log file")
		self.parser_all.add_argument("-v", "--verbose", action='store_true', help="increase output verbosity.")
		self.parser_all.set_defaults(all=True)
		self.parser_all.set_defaults(menu=False)
		self.parser_all.set_defaults(gui=False)

		# create the parser for the "menu" command
		self.parser_menu = self.subparsers.add_parser('menu', help='menu -h')
		self.parser_menu.add_argument("-f", "--file", help="Change the default configuration file")
		self.parser_menu.add_argument("-o", "--output", metavar='FILE', help="Change the default log file")
		self.parser_menu.set_defaults(menu=True)
		self.parser_menu.set_defaults(all=False)
		self.parser_menu.set_defaults(gui=False)


		# create the parser for the "gui" command
		self.parser_gui = self.subparsers.add_parser('gui', help='gui -h')
		self.parser_gui.add_argument("-f", "--file", help="Change the default configuration file")
		self.parser_gui.add_argument("-o", "--output", metavar='FILE', help="Change the default log file")
		self.parser_gui.set_defaults(gui=True)
		self.parser_gui.set_defaults(all=False)
		self.parser_gui.set_defaults(menu=False)

		#parser.print_help()
		self.args = self.parser.parse_args()

	def getArgs(self):
		return self.args

"""
############################################################################
#
#                      login event
#
############################################################################
"""

class myLoginEvent(object):
	# ------------------ Init
	def __init__(self,*args,**kwargs):
		self.logfile=kwargs.pop('logfile')

		logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
					datefmt='%Y%m%d%H%M',
					filename=self.logfile,
					filemode='a')
		self.logger = logging.getLogger("./"+sys.argv[0])
		self.console="";
		self.formatter="";

	def screenLogging(self):
		# writes INFO> to the sys.stderr
		self.console = logging.StreamHandler()
		self.console.setLevel(logging.INFO)
		# set a format for console use
		self.formatter = logging.Formatter('%(name)-12s %(levelname)-8s %(message)s')
		self.console.setFormatter(self.formatter)
		# add the handler to the root logger
		logging.getLogger('').addHandler(self.console)

	def printDebug(self,msg):
		self.logger.debug(msg)
		return

	def printWarning(self,msg):
		self.logger.warning(msg)
		return

	def printInfo(self,msg,value):
		self.logger.info(msg+" [ \033[32m "+value+" \033[37m ]")
		return

	def printError(self,msg,stopScript=False):
		self.logger.error(msg+" [ \033[31m FAILED \033[37m ]")
		if(stopScript):
			sys.exit(1)

"""
############################################################################
#
#                      Progress Bar (console)
#
############################################################################
"""

class progressBar(myLoginEvent):

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.rows, self.columns = os.popen('stty size', 'r').read().split()
		self.text=""
		self.barLength=int(self.columns)-30
		print("\n")

	def updateProgressBar(self,progress,text="",severity=True):
		if text!="":
			self.text=text

		status = ""
		if isinstance(progress, int):
			progress = float(progress)
		if not isinstance(progress, float):
			progress = 0
			status = "error: progress var must be float\r\n"
		if progress >= 1:
			progress = 1

		block = int(round(self.barLength*progress)+1)

		if severity:
			text = "\033["+str(int(self.rows)-1)+";1H{0}{1}{2}\r".format(text," "*(self.barLength-len(text)+13),"[OK]")
		else:
			text = "\033["+str(int(self.rows)-1)+";1H{0}{1}{2}\r".format(text," "*(self.barLength-len(text)+13),"[KO]")

		sys.stdout.write(text)
		sys.stdout.flush()

		text = "\033["+self.rows+";1H\rPercent: [{0}] {1}% {2}   ".format("#"*block + "-"*(self.barLength-block), str((progress*100))[0:4], status)
		sys.stdout.write(text)
		sys.stdout.flush()

		if progress == 1:
			print("\n")

"""
############################################################################
#
#                      Package install
#
############################################################################
"""

class OSCommand(myLoginEvent):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.commandLine=""
		self.status=False
		self.systemLog=""

	def resetOSCommand(self):
		self.commandLine=""
		self.status=False
		self.systemLog=""

	def getStatus(self):
		return self.status

	def getLog(self):
		return self.systemLog

	def defineCommandLine(commandLine):
		self.commandLine=commandLine

	def runOSCommand(self):
		proc = Popen(self.commandLine, stdout=PIPE, stderr=PIPE, shell=True)
		out, err = proc.communicate()
		exitcode = proc.returncode

		self.systemLog="Command >>> "+self.commandLine+" <<< STDOUT >>> "+str(out)+" <<< STDERR >>> "+str(err)
		if exitcode>0:
			self.status=False
		else:
			self.status=True
		return self.status

class installPersonalPackageArchive(OSCommand):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.PPAName=""
		self.PPAKey=""

	def definePPA(self,name="", key=""):
		self.PPAName=name
		self.PPAKey=key

	def installPPA(self):
		self.status=True
		if self.PPAName != "":
			if "://" in self.PPAName:
				self.installPPAURL()
			else:
				self.installPPAName()
		if self.PPAKey != "" and self.status == True:
			self.installPPAKey()

	def installPPAName(self):
		self.commandLine = "add-apt-repository -y ppa://"+self.PPAName
		return self.runOSCommand()

	def installPPAURL(self):
		self.commandLine = "add-apt-repository -y \"deb [arch=amd64] "+self.PPAName+" stable main\""
		return self.runOSCommand()

	def installPPAKey(self):
		self.commandLine = "wget -O /tmp/key "+self.PPAKey+" && "
		self.commandLine = self.commandLine+"apt-key add /tmp/key"
		return self.runOSCommand()

class installPackage(OSCommand):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.packageName=""

	def definePackageName(self,packageName):
		self.packageName=packageName

	def installPKG(self):
		self.commandLine = "apt-get install -y "+self.packageName
		return self.runOSCommand()

class myPackageManager(installPackage,installPersonalPackageArchive):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		monSystem=""

	def updateSystem(self):
		self.commandLine="apt-get update -y"
		return self.runOSCommand()

	def upgradeSystem(self):
		self.commandLine="apt-get autoremove -y && apt-get update -y && apt-get upgrade -y && apt-get dist-upgrade -y"
		return self.runOSCommand()
	# ------------------ other tasks

	def fixMSFont(self):
		self.commandLine = "wget -O /tmp/ttf-mscorefonts-installer_3.6_all.deb "
		self.commandLine = self.commandLine+"http://ftp.de.debian.org/debian/pool/contrib/m/msttcorefonts/ttf-mscorefonts-installer_3.6_all.deb &&"
		self.commandLine = self.commandLine+"sudo dpkg -i /tmp/ttf-mscorefonts-installer_3.6_all.deb"
		return self.runOSCommand()

"""
############################################################################
#
#                      Check
#
############################################################################
"""

class checkEnvironment(myLoginEvent):
	def __init__(self,*args,**kwargs):
		# logfile
		super().__init__(*args,**kwargs)
		#myLoginEvent.__init__(self,logfile) #build loginEvent
		self.myTest=True

		if self.isRoot() is not True:
			self.screenLogging()
			self.printError(sys.argv[0]+" : Use Sudo !")
			self.myTest=False

		if self.checkInternet() is not True:
			if self.myTest is True:
				self.screenLogging()
			self.printError("Internet")
			self.myTest=False

		if 	self.myTest is not True:
			sys.exit(1)

	# ------------------ CHECK
	def isRoot(self):
		if os.environ["USER"] == "root":
			return True
		else:
			return False

	def checkInternet(self, host="8.8.8.8", port=53, timeout=3):
		"""
		Host: 8.8.8.8 (google-public-dns-a.google.com)
		OpenPort: 53/tcp
		Service: domain (DNS/TCP)
		"""
		try:
			socket.setdefaulttimeout(timeout)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
			return True
		except:
			return False



"""
############################################################################
#
#                      FSTAB
#
############################################################################
"""

class myFSTab(myLoginEvent):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs) #logfile
		self.newFSTab=""
		self.FSTab="/etc/fstab"
	def backupFSTab(self):
		try:
			srcfile=self.FSTab
			dstdir=srcfile+"."+str(int(time.time()))
			self.printDebug("Copy "+srcfile+" > "+dstdir)
			shutil.copy(srcfile, dstdir)
			return True
		except:
			return False

	def readFSTab(self):
		try:
			with open(self.FSTab, "r") as fstab:
				self.newFSTab = ''.join(fstab.readlines())
				fstab.close()
			return True
		except:
			return False
			
	def updateFSTab(self):
		try:
			fstab=open(self.FSTab, "w")
			fstab.write(self.newFSTab)
			fstab.close()
			return True
		except:
			return False
	# ------------------ SWAP
	def commentSwap(self):
		"""
		sudo sed -i '/ swap / s/^/#/' /etc/fstab
		"""
		needUpdate=False
		for item in self.newFSTab.split("\n"):
			if ((" swap  " in item) and (item[0]!="#")):
				needUpdate=True
				UUID=item.strip().split("=")
				UUID=UUID[1].split(" ")
				UUID=UUID[0]
				lineToComment=item.strip()
				self.printDebug("FSTAB : comment >"+lineToComment)
				self.newFSTab=self.newFSTab.replace(lineToComment, "#"+lineToComment)
		return needUpdate

	def disableSwap(self):
		if self.backupFSTab() and self.readFSTab():
			if self.commentSwap()!=True:
				self.printDebug("Swap already disabled")
				return True
			else:
				if self.updateFSTab():
					return True
				else:
					return False
			return True

		return False


"""
############################################################################
#
#                      Virtual Drive
#
############################################################################
"""

class myVirtualDrive(myFSTab):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.virtualRAMMountPoint="/media/virtualram"
		self.APTArchive="/var/cache/apt/archives"

	# ------------------ Virtual Drive
	def makeVirtualRAMMountPoint(self):
		try:
			if not os.path.exists(self.virtualRAMMountPoint):
				os.makedirs(self.virtualRAMMountPoint)
				return True
			else:
				self.printDebug("Virtual Drive Mountpoint already created")
				return False
		except:
			return False

	def makeVirtualRAMUpdateFSTab(self):
		line = "tmpfs "+str(self.virtualRAMMountPoint)+" tmpfs defaults,size=2G 0 0\n"
		try:
			with open(self.FSTab, 'a') as fstab:
				fstab.writelines(line)
			return True
		except:
			
			return False

	def mountVirtualDrive(self):
		if os.path.ismount(self.virtualRAMMountPoint):
			return False
		else:
			subprocess.Popen(["mount",self.virtualRAMMountPoint])
			return True

	def putAPTOnVirtualRAM(self):
		self.createVirtualRAM();
		if os.path.islink(self.APTArchive):
			self.printDebug("Link APT Archives to Swap Drive : already Done")
			return True
		else:
			shutil.rmtree(self.APTArchive)
			os.symlink(self.virtualRAMMountPoint, self.APTArchive)
			return True

	def createVirtualRAM(self):
		self.backupFSTab()
		self.makeVirtualRAMMountPoint()
		self.makeVirtualRAMUpdateFSTab()
		self.mountVirtualDrive()



"""
############################################################################
#
#                      master ubuntu
#
############################################################################
"""


class masterUbuntu(checkEnvironment,myVirtualDrive,myPackageManager):
	# ------------------ Init
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)

		self.optfile=kwargs.pop('optfile')

		self.systemName = os.uname()[1]
		self.ubuntuVersion = platform.linux_distribution()[0]+"/"+platform.linux_distribution()[1]
		self.ubuntuCodename = platform.linux_distribution()[2]
		self.mySetup={}
		self.user=os.environ["SUDO_USER"]

		#libSoftwareEnable=importlib.util.find_spec("SoftwareProperties")
		#if libSoftwareEnable is None:
		#	self.packageName="python3-software-properties"
		#	self.installPKG()

		self.setup()

	# ------------------ Get environment
	def initEnvironment(self):
		try:
			with open(self.optfile, "r") as mySetupJSONFile:
				mySetupJSON = ''.join(mySetupJSONFile.readlines())
				mySetupJSONFile.close()
		except:
			print(sys.argv[0]+" : can't open "+self.optfile+" !")
			sys.exit(1)

		try:		
			mySetupJSON=json.loads(mySetupJSON)
		except:
			print(sys.argv[0]+" : can't decode "+self.optfile+" !")
			sys.exit(1)

		myFunctions= {
				"disableSwap":self.disableSwap,
				"putAPTOnVirtualRAM":self.putAPTOnVirtualRAM,
				"upgradeSystem":self.upgradeSystem,
				"installSelectedPackage":self.installSelectedPackage,
				"setUpUnity":self.setUpUnity,
				"fixMSFont":self.fixMSFont,
				"installPKG":self.installPKG
		}
		for currentTask in mySetupJSON["task"].keys():
			mySetupJSON["task"][currentTask]["function"]=myFunctions[mySetupJSON["task"][currentTask]["function"]]
		for currentPackageCategory in mySetupJSON["package"].keys():
			for currentPackage in mySetupJSON["package"][currentPackageCategory].keys():
				mySetupJSON["package"][currentPackageCategory][currentPackage]["function"]=myFunctions[mySetupJSON["package"][currentPackageCategory][currentPackage]["function"]]

		self.mySetup=mySetupJSON
		self.countTasks()
		return True

	def setup(self):
		self.initEnvironment()

	#################################################################################################################################
	# Count the tasks to do : not funny but usefull to calculate the progress bar's max value
	#########################################################################
	def countTasks(self):
		self.amountOfTask=0
		for currentTask in self.mySetup["task"]:
			if self.mySetup["task"][currentTask]["run"] is True and self.mySetup["task"][currentTask]["LABEL"]!="Install Packages":
				self.amountOfTask=self.amountOfTask+1

		for currentPackageCategory in self.mySetup["package"]:
			for currentPackage in self.mySetup["package"][currentPackageCategory]:
				if self.mySetup["package"][currentPackageCategory][currentPackage]["run"] is True:
					self.amountOfTask=self.amountOfTask+1


	# ------------------ Manage setup
	################################################################################################################################
	# Install the package : call do task
	#########################################################################
	def installSelectedPackage(self):

		for currentPackageCategory in sorted(self.mySetup["package"]):
			for currentPackage in sorted(self.mySetup["package"][currentPackageCategory]):
				if self.mySetup["package"][currentPackageCategory][currentPackage]["run"]:
					self.printDebug("Starting : "+self.mySetup["package"][currentPackageCategory][currentPackage]["LABEL"])
					if self.useProgressBar:
						self.updateProgressBar(self.amountOfTaskDone/self.amountOfTask,"Starting : "+self.mySetup["package"][currentPackageCategory][currentPackage]["LABEL"])
					if self.mySetup["package"][currentPackageCategory][currentPackage]["PPA"]!="":
						self.PPAName=self.mySetup["package"][currentPackageCategory][currentPackage]["PPA"]
						self.installPPA()
						self.printDebug(self.systemLog)
						if self.mySetup["package"][currentPackageCategory][currentPackage]["KEY"]!="":
							self.PPAKey=self.mySetup["package"][currentPackageCategory][currentPackage]["KEY"]
							self.installPPAKey()
							self.printDebug(self.systemLog)
						self.updateSystem()
					self.packageName=self.mySetup["package"][currentPackageCategory][currentPackage]["PKG"]
					myFunction=self.mySetup["package"][currentPackageCategory][currentPackage]["function"]
					status=myFunction()
					self.printDebug(self.systemLog)
					if status:
						self.printInfo(self.mySetup["package"][currentPackageCategory][currentPackage]["LABEL"],"OK")
						if self.useProgressBar:
							self.amountOfTaskDone=self.amountOfTaskDone+1
							self.updateProgressBar(self.amountOfTaskDone/self.amountOfTask,"Apply : "+self.mySetup["package"][currentPackageCategory][currentPackage]["LABEL"])
							time.sleep( 0.5 )
					else:
						self.printError(self.mySetup["package"][currentPackageCategory][currentPackage]["LABEL"])
		return status

	#################################################################################################################################
	# Do task : run functions according to user selection
	#########################################################################
	def doTaks(self,category="task"):
		status=False
		self.printDebug("amountOfTask="+str(self.amountOfTask))
		self.printDebug("self.useProgressBar="+str(self.useProgressBar))

		for currentItem in sorted(self.mySetup[category]):
			if self.mySetup[category][currentItem]["run"]:
				#Get the function define in mySetup
				self.printDebug("Starting : "+self.mySetup[category][currentItem]["LABEL"],)
				if self.useProgressBar:
					self.updateProgressBar(self.amountOfTaskDone/self.amountOfTask,"Starting : "+self.mySetup[category][currentItem]["LABEL"])
				myFunction=self.mySetup[category][currentItem]["function"]
				self.systemLog=""
				status=myFunction()
				if self.systemLog !="":
					self.printDebug(self.systemLog)

				if status:
					self.printInfo(self.mySetup[category][currentItem]["LABEL"],"OK")
					if self.useProgressBar:
						if self.mySetup[category][currentItem]["LABEL"]!="Install Packages":
							self.amountOfTaskDone=self.amountOfTaskDone+1
						self.updateProgressBar(self.amountOfTaskDone/self.amountOfTask,"Apply : "+self.mySetup[category][currentItem]["LABEL"])
						time.sleep( 0.5 )
				else:
					self.printError(self.mySetup[category][currentItem]["LABEL"])
		return status


	def setUpUnity(self):
		# /usr/share/applications

		self.commandLine = "su "+self.user+" -c \""
		self.commandLine = self.commandLine+"""\
gsettings set com.canonical.Unity form-factor 'Netbook' && \
gsettings set com.canonical.Unity.Lenses remote-content-search 'none' && \
gsettings set com.canonical.Unity.Launcher favorites \\\"['application://chrome-app-list.desktop', 'application://org.gnome.Nautilus.desktop', 'application://google-chrome.desktop', 'application://pidgin.desktop', 'application://gimp.desktop', 'application://shutter.desktop', 'application://openshot.desktop', 'application://keepass2.desktop', 'unity://devices','unity://running-apps', 'unity://expo-icon']\\\" && \
dconf write /org/compiz/profiles/unity/plugins/opengl/texture-filter 0 && \
gsettings set org.compiz.core:/org/compiz/profiles/unity/plugins/core/ hsize 4"""
		self.commandLine = self.commandLine + "\""
		#print(self.commandLine)
		#return True
		return self.runOSCommand()



"""
############################################################################
#
#                      master ubuntu (CLI Version)
#
############################################################################
"""

class masterUbuntuCLI(masterUbuntu,progressBar):

	#################################################################################################################################
	# ------------------ Init
	#########################################################################
	def __init__(self,*args,**kwargs):					# optfile="", logfile="", useprogressbar=False
										#
		self.amountOfTask=0						# Specific VARS
		self.amountOfTaskDone=0						#
										#
		super().__init__(*args,**kwargs)		#
										#
		self.useProgressBar=kwargs.get('useprogressbar',False)		#
		if(self.useProgressBar!=True):					#
			self.screenLogging()					# print INFO on screen wo progressbar
		self.printEnvironment()						# print default header
	#################################################################################################################################
	# Setup the environment according to the class usage
	#########################################################################
	def setup(self):							#
		self.initEnvironment()						#
		self.countTasks()						#
	#################################################################################################################################
	# Loggin : add-on to print basic informations
	#########################################################################
	def printEnvironment(self):						#
		self.printInfo("Hostname", self.systemName)			#
		self.printInfo("Version", self.ubuntuVersion)			#
		self.printInfo("Codename", self.ubuntuCodename)			#
		self.printInfo("User", os.environ["SUDO_USER"])			#
		self.printInfo("Log", self.logfile)				#
		self.printInfo("Options", os.path.abspath(self.optfile))	#

"""
#########################################################################################################################################
#
#                      master ubuntu (GUI Version)
#
#########################################################################################################################################
"""

class masterUbuntuMenu(masterUbuntuCLI):
	#################################################################################################################################
	# ------------------ Init
	#########################################################################
	def __init__(self,*args,**kwargs):					# in : str/optfile & str/logfile - out: <object>
		super().__init__(*args,**kwargs)				# build masterUbuntu with optfile/logfile
										#
		libDialogEnable=importlib.util.find_spec("Dialog")		# test Dialog availability
		if libDialogEnable is None:					# if Dialog is unavailable
			self.packageName="python3-dialog"			#
			self.installPKG()					# then install the package
										#
		from dialog import Dialog					# import Dialog
		locale.setlocale(locale.LC_ALL, '')				#
		self.dialog = Dialog(dialog="dialog")				# init self.dialog to create the screens
		self.myPackageCategory=[]					#
		self.installationMode=""					#
		self.taskSelected=[]						#
		self.categorySelected=[]					#
		self.packageSelected={}						#
		self.resetTaskAndPackageRun()					#
		self.launchGUI()						#
		#self.prepareInstall()						#
		self.countTasks()						# Count the tasks
	#################################################################################################################################
	# Setup my environment
	#########################################################################
	def setup(self):							# in : nothing - out: nothing
		self.initEnvironment()						# call initenvironment only
	#################################################################################################################################
	# ------------------ GUI
	#################################################################################################################################
	# Select Item choosen by user
	#########################################################################

	def getPackageCategory(self):
		myItem=[]
		index=0
		for currentPackageCategory in sorted(self.mySetup["package"]):
			if self.packageSelected.get(currentPackageCategory)!=None:
				myItem.append((currentPackageCategory,"",True))
			else:
				myItem.append((currentPackageCategory,"",False))
			index=index+1
		return myItem							# return the result

	def getPackageFromPackageCategory(self,packageCategory, formated=True):
		myItem=[]
		for currentPackage in sorted(self.mySetup["package"][packageCategory]):	# search all items (tasks or packages)
			tag=self.mySetup["package"][packageCategory][currentPackage]["LABEL"]
			tagid=currentPackage
			status=self.mySetup["package"][packageCategory][currentPackage]["run"]
			myItem.append((tagid,tag,status,tag))			#

		return myItem							# return the result
										#
	#################################################################################################################################
	# Dialog Menu : launch and manage the GUI feedback
	#########################################################################
										#
	def launchGUI(self):							#
										#
		self.dialog.set_background_title(				#init Dialog
					self.mySetup["GUI"]["backgroundTitle"])	#
		if(self.warningMessage()):					# Warning message
			while True:
				self.installationMode=""
				if self.selectTask() != True:
					self.printDebug("User canceled")	#
					sys.exit(1)				# User has canceled
				self.updateTask()
				if 'Install Packages' in self.taskSelected:
					if self.managePackageMenu() == True:		#
						self.printDebug("User selected package")#
						self.updatePackage()
						return True				#
				else:
					return True
		else:								#
			sys.exit(1)						# User has canceled
										
										#
	def managePackageMenu(self):
		if self.selectInstallationMode() != True:
			return False
		if self.installationMode=="s":			
			if self.selectPackageCategoryMenu():
				for currentPackageCategory in self.categorySelected:
					if self.selectPackageMenu(currentPackageCategory) != True:
						return False
			else:
				return False
		self.printDebug("User selected : "+json.dumps(self.packageSelected))

		return True

	def resetTaskAndPackageRun(self, runValue=False):
		self.resetPackageRun(runValue)
		self.resetTaskRun(runValue)

	def resetTaskRun(self, runValue=False):
		for currentTask in self.mySetup["task"]:			# All tasks disable by default
			self.mySetup["task"][currentTask]["run"] = runValue 	# All package disable by default

	def resetPackageRun(self, runValue=False):
		for currentPackageCategory in self.mySetup["package"]:
			for currentPackage in self.mySetup["package"][currentPackageCategory]:
				self.mySetup["package"][currentPackageCategory][currentPackage]["run"] = runValue

	def updatePackage(self):
		self.resetPackageRun()						# reset current value store
		if self.installationMode == "s":				# user selected the package
			for currentPackageCategory in self.packageSelected:
				for currentPackage in self.packageSelected[currentPackageCategory]:
					self.mySetup["package"][currentPackageCategory][currentPackage]["run"]=True
		if self.installationMode == "a":				# automatic
			self.resetPackageRun(True)				# => All must be done

	def updateTask(self):
		for currentTask in sorted(self.mySetup["task"]):
			if self.mySetup["task"][currentTask]["LABEL"] in self.taskSelected:
				self.mySetup["task"][currentTask]["run"] = True
			else:
				self.mySetup["task"][currentTask]["run"] = False


	def prepareInstall(self):
		print(self.taskSelected)	# ['Upgrade system', 'Install Packages', 'Fixe ttf-mscorefonts-installer (bug #1607535)', 'Setup Unity 7']
		print(self.packageSelected)	# {'Dev': ['Sublime Text 3', 'vim'], 'Google': ['Chrome']}
		print(self.installationMode)
		print(self.mySetup)
		sys.exit(1)



	#################################################################################################################################
	# Dialog Menu : Warning bla bla...
	#########################################################################
										#
	def warningMessage(self):						#
		#if self.dialog.yesno(self.mySetup["GUI"]["warningMsg"],		# print warning and wait an answer (yes/no) from user
		(code, tag)=self.dialog.radiolist(self.mySetup["GUI"]["warningMsg"],		# print warning and wait an answer (yes/no) from user
					choices=[("I accept","",False),("I dont accept","",False)],
					height=18, width=60) #== self.dialog.OK:	#
		if(self.dialog.OK==code) and (tag=="I accept"):
			self.printDebug("User accepted Warning")		#
			return True						# if true - all done successfully => just do it...
		else:								#
			self.printDebug("User dit not accept Warning")		#
			return False						# User refused to use the script => exit
										#
	#################################################################################################################################
	# Dialog Menu : select the tasks to run
	#########################################################################
										#
	def selectTask(self):							#
		userSelectedTask=False						#
		while userSelectedTask is not True:				#
			code, tags = self.dialog.checklist("",			# suggest task user - user select ok or cancel
					choices=self.getItem(			#
					self.mySetup["task"]),			#
					title=self.mySetup["GUI"]["titleTasks"])#
			if (code == self.dialog.OK):				# user select OK
				self.taskSelected=tags				#
				self.printDebug("User selected these tasks : "	#
						+json.dumps(tags))		#
				return True					#
			else:							#
				self.printDebug("User cancel tasks.")		#
				return False					# user select CANCEL
		return True							#
										#
	#################################################################################################################################
	# Dialog Menu : select the packages
	#########################################################################
	def selectPackageCategoryMenu(self):

		code, tag = self.dialog.checklist("",
					 choices=self.getPackageCategory(),
					 title=self.mySetup["GUI"]["titleCat"])
		if (code == self.dialog.OK):
			self.categorySelected=tag
			self.printDebug(
				"User selected these category : "
				+json.dumps(tag))
			return True
		else:
			return False

	def selectInstallationMode(self):
		code, tag = self.dialog.menu(self.mySetup["GUI"]["titleMode"],	# suggest automatic or manual
				choices=self.mySetup["GUI"]["choicesMode"])	#
		if (code == self.dialog.OK):					# user choose select the packages & OK
			self.installationMode=tag
			self.printDebug(
				"User selected this installation mode : "
				+json.dumps(tag))
			return True
		else:
			return False


	def selectPackageMenu(self,category):						#

		text = "Press the space bar to toggle the status of an item \
between selected (on the left) and unselected (on the right). You can use the \
TAB key or ^ and $ to change the focus between the different parts of the \
widget."
		code, tags = self.dialog.buildlist(text, items=self.getPackageFromPackageCategory(category), visit_items=True,
			      item_help=True,
			      title=self.mySetup["GUI"]["titlePKG"]+"/"+category)
		if code == self.dialog.OK:					# if OK
			self.packageSelected[category]=tags			# change the packages to setup in self.mySetup
			self.printDebug("User selected these package : "	#
						+json.dumps(tags))		#
			return True 						#
		else:								#
			return False						# go back to tasks menu => user will provide another choices
										#
	#################################################################################################################################
	# Dialog : Update the progress bar
	#########################################################################
										#
	def updateProgressBar(self,progress,text="",severity=True):		# update the progress bar during setup
										#
		if progress==0:							# if progress=0
			self.dialog.gauge_start()				# then init the progress bar
										#
		if progress<=1:							#
			self.dialog.gauge_update(int(progress*100),		# update the text
					 text="\n"+text, update_text=True)	#
										#
		if progress>=1:							# if it's finished
			time.sleep( 1 )						# let 1 sec to keep the previous text and update
			self.dialog.gauge_update(int(progress*100),		#
					 text="\nFinished...", update_text=True)#
			time.sleep( 1 )						# let 1 sec to show the last message (Finished)
			self.dialog.gauge_stop()				# stop the progressbar
			print("\n")						# let 1 line to finish correctly
										#
	#################################################################################################################################
	# Dialog : Provide the label to build menu
	#################################################################################################################################
										#
	def getItem(self, item, formated=True):					# return 1 array with all tasks or packages
		myItem=[]							#
		for currentItem in sorted(item.keys()):				# search all items (tasks or packages)
			label=item[currentItem]["LABEL"]			#
			if formated:						# if formatted then return (label,"",True) to build the menu
				myItem.append((label,"",True))			#
			else:							# else return an array (label1, label2,...)
				myItem.append(label)				#
		return myItem							# return the result
										#
	#################################################################################################################################

"""
#########################################################################################################################################
#
#                      GUI
#
#########################################################################################################################################
"""

class masterUbuntuGUI(masterUbuntuMenu,Gtk.Window):
	def __init__(self,*args,**kwargs):

		self.grid=""
		self.menuBar=""
		self.doItButton=""
		self.myWindow=""
		self.pagePackage={}
		self.pageTask=""
		self.switchState=""
		self.progressBar=""
		self.progressBarFraction=""
		self.progressBarText=""
		self.progressBarLabel=""
		self.pageProgressBar=""
		self.InstallPackagesSelected=False
		super().__init__(*args,**kwargs)

	def launchGUI(self):
		self.useProgressBar=True
		self.setupGUI()
		if(self.printGTKWarning(
				self.mySetup["GUI"]["backgroundTitle"],
				self.mySetup["GUI"]["warningMsg"])):
			self.show_all()
			self.hidePagePackage()
			self.pageTask.hide()
			self.pageLaunch.hide()
			self.pageProgressBar.hide()
			Gtk.main()

	def setupGUI(self):
		self.createWindow()
		self.createGrid()
		self.createMenuBar()
		self.createStack()
		self.createPageMode()
		self.createPageTask()
		self.createPagePackage()
		self.createPageLaunch()
		self.createProgressBar()

	def createWindow(self):
		Gtk.Window.__init__(self)
		self.set_default_size(400, 220)
		self.connect("destroy", Gtk.main_quit)
		#self.set_position(Gtk.WIN_POS_CENTER)

	def createGrid(self):
		self.grid = Gtk.Grid()
		self.add(self.grid)

	def createMenuBar(self):
		self.menuBar = Gtk.MenuBar()
		fileMenu = Gtk.Menu()
		fileMenuItem = Gtk.MenuItem("?")
		fileMenuItem.set_submenu(fileMenu)
		aboutOption = Gtk.MenuItem("About")
		aboutOption.connect("activate", self.aboutGTK)
		fileMenu.append(aboutOption)
		exitOption = Gtk.MenuItem("Exit")
		exitOption.connect("activate", Gtk.main_quit)
		fileMenu.append(exitOption)
		self.menuBar.append(fileMenuItem)
		self.grid.attach(self.menuBar,0, 0, 1, 1)

	def createStack(self):
		self.stack = Gtk.Stack()
		self.stack.set_hexpand(True)
		self.stack.set_vexpand(True)
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
		self.stack.set_transition_duration(1000)
		self.grid.attach(self.stack, 0, 2, 1, 1)
		self.stackswitcher = Gtk.StackSwitcher()
		self.stackswitcher.set_stack(self.stack)
		self.grid.attach(self.stackswitcher, 0, 1, 1, 1)

	def createPageMode(self):
		self.pageMode = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		self.pageMode.set_border_width(80)
		self.pageMode.add(self.createLabel("Automatic installation      "))
		self.pageMode.pack_start(self.createSwitch(), True, True, 0)
		self.doItButton=self.createButton("Do it !",self.doAll)
		self.pageMode.pack_start(self.doItButton, True,True,0)
		self.stack.add_titled(self.pageMode, "Installation Mode", "Installation Mode")

	def createPageTask(self):
		self.pageTask = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		#self.pageTask.set_border_width(150)
		for currentTask in sorted(self.mySetup["task"]):
			self.pageTask.add(
				self.createCheckBox("task",
					self.mySetup["task"][currentTask]["LABEL"],
					currentTask))
		self.stack.add_titled(self.pageTask, "Task", "Task")

	def createPagePackage(self):
		pagePackage={}
		for currentPackageCategory in sorted(self.mySetup["package"]):
			pagePackage[currentPackageCategory] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
			self.packageSelected[currentPackageCategory]=[]
			#self.pagePackage[currentPackageCategory].set_border_width(150)
			for currentPackage in sorted(self.mySetup["package"][currentPackageCategory]):
				pagePackage[currentPackageCategory].add(
					self.createCheckBox(currentPackageCategory,
					self.mySetup["package"][currentPackageCategory][currentPackage]["LABEL"],
					currentPackage))
			self.stack.add_titled(pagePackage[currentPackageCategory], currentPackageCategory, currentPackageCategory)
		self.pagePackage=pagePackage

	def createPageLaunch(self):
		self.pageLaunch = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		self.pageLaunch.set_border_width(80)
		self.pageLaunch.add(self.createLabel("Launch my setup      "))
		self.launchButton=self.createButton("Launch !",self.launchInstallation)
		self.pageLaunch.pack_start(self.launchButton, True,True,0)
		self.stack.add_titled(self.pageLaunch, "Launch", "Launch")

	def launchInstallation(self, widget=""):
		import threading
		self.countTasks()
		self.showMyProgression()
		self.updateProgressBar(0,"Starting...")
		t = threading.Thread(target=self.doTaks)
		self.timeout_id = GObject.timeout_add(200, self.updateProgressBarGTK)
		t.start()

	def updateProgressBarGTK(self):
		self.progressBar.set_fraction(self.progressBarFraction)
		self.progressBar.set_show_text(True)
		self.progressBarLabel.set_text(self.progressBarText)
		if self.progressBarFraction == 1:
			self.progressBarLabel.set_text("Finished...")
			self.printGTKInfo("Master Ubuntu","Tasks have been applied...")
			sys.exit(0)
		return True

	def updateProgressBar(self,fraction,text="",severity=True):
		self.progressBarFraction=fraction
		self.progressBarText=text

	def showMyProgression(self):
		self.hidePagePackage()
		self.pageTask.hide()
		self.pageMode.hide()
		self.pageLaunch.hide()
		self.pageProgressBar.show()

	def createProgressBar(self):
		self.pageProgressBar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.pageProgressBar.set_border_width(80)
		self.progressBar = Gtk.ProgressBar()
		self.pageProgressBar.add(self.progressBar)
		self.progressBarLabel=self.createLabel("Starting...")
		self.pageProgressBar.add(self.progressBarLabel)
		self.stack.add_titled(self.pageProgressBar, "Installation...", "Installation...")


	def createCheckBox(self, category, task, taskID):
		button = Gtk.CheckButton(task)
		button.connect("toggled", self.toggledCheckbox, category, task, taskID)
		return button

	def toggledCheckbox(self, widget, category, task, taskID):
		if task == "Install Packages":
			if self.InstallPackagesSelected!=True:
				self.InstallPackagesSelected=True
				self.showPagePackage()
			else:
				self.InstallPackagesSelected=False
				self.hidePagePackage()
		if widget.get_active():
			print("active "+category+" / "+task)
			if category == "task":
				self.taskSelected.append(task)
				self.mySetup["task"][taskID]["run"]=True
				#self.updateTask()
			else:
				self.packageSelected[category].append(task)
				self.mySetup["package"][category][taskID]["run"]=True
		else:
			if category == "task":
				self.taskSelected.remove(task)
				self.mySetup["task"][taskID]["run"]=False
				#self.updateTask()
			else:
				self.packageSelected[category].remove(task)
				self.mySetup["package"][category][taskID]["run"]=False

		# print(self.taskSelected)
		# print(self.packageSelected)
		# print(self.mySetup)

	def createLabel(self, text):
		return Gtk.Label(text)

	def createSwitch(self):
		switch = Gtk.Switch()
		switch.connect("notify::active", self.on_switch_activated)
		switch.set_active(True)
		return switch

	def hidePagePackage(self):
		# print(self.pagePackage)
		for currentPage in self.pagePackage:
			self.pagePackage[currentPage].hide()
	def showPagePackage(self):
		# print(self.pagePackage)
		for currentPage in self.pagePackage:
			self.pagePackage[currentPage].show()

	def doAll(self,widget):
		self.doall=True
		self.resetTaskAndPackageRun(True)
		self.launchInstallation()

		#self.printGTKInfo(title="", text="")
		#self.aboutGTK()

	def createButton(self, label,function):
		button = Gtk.Button.new_with_label(label)
		button.connect("clicked", function)
		return button

	def on_switch_activated(self, switch, gparam):
		if switch.get_active():
			if self.switchState!="":
				self.pageTask.hide()
				self.pageLaunch.hide()
				self.hidePagePackage()
				self.doItButton.set_sensitive(True)
			self.installationMode = "a"				# automatic
			self.switchState = "on"
		else:
			if self.switchState!="":
				self.pageTask.show()
				self.pageLaunch.show()
				if self.InstallPackagesSelected==True:
					self.showPagePackage()
			self.installationMode = "s"				# user select the package
			self.doItButton.set_sensitive(False)
			self.switchState = "off"

	def createWarningPage(self):
		self.page1 = Gtk.Box()
		self.page1.set_border_width(10)
		self.page1.add(Gtk.Label('Warning'))
		self.notebook.append_page(self.page1, Gtk.Label('Plain Title'))

	def printGTKInfo(self, title="", text=""):
		dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
			Gtk.ButtonsType.OK, title)
		dialog.format_secondary_text(text)
		dialog.run()
		dialog.destroy()
		return True

	def printGTKError(self, title="", text=""):
		dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
			Gtk.ButtonsType.CANCEL, title)
		dialog.format_secondary_text(text)
		dialog.run()
		dialog.destroy()
		return True

	def printGTKWarning(self, title="", text=""):
		dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
			Gtk.ButtonsType.OK_CANCEL, title)
		dialog.format_secondary_text(text)
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			status=True
		elif response == Gtk.ResponseType.CANCEL:
			status=False
		dialog.destroy()
		return status

	def printGTKQuestion(self, question="", text=""):
		dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION,
			Gtk.ButtonsType.YES_NO, question)
		dialog.format_secondary_text(text)
		response = dialog.run()
		if response == Gtk.ResponseType.YES:
			status=True
		elif response == Gtk.ResponseType.NO:
			status=False
		dialog.destroy()
		return status

	def aboutGTK(self,widget): #, widget):
		image = Gtk.Image()
		image.set_from_file("/usr/share/icons/unity-icon-theme/apps/128/softwarecentre.svg")
		pixbuf = image.get_pixbuf()

		#pixbuf = GdkPixbuf.Pixbuf.new_from_file()
		#GdkPixbuf.new_from_file
		aboutGTK = Gtk.AboutDialog()
		#aboutGTK.set_icon_from_file("/usr/share/icons/unity-icon-theme/apps/128/softwarecentre.svg")
		aboutGTK.set_name("Master Ubuntu")
		aboutGTK.set_version("1.0 (beta)")
		aboutGTK.set_copyright("Copyright © 2017")
		aboutGTK.set_comments(aboutGTK.get_name() + " " + aboutGTK.get_version() +" is a tool allowing homogeneous installation for several Ubuntu PCs")
		aboutGTK.set_license("Copyright © 2017 Ko4la\n\nThis program is free software; you can redistribute it and/or modify\nit under the terms of the GNU General Public License as published by\nthe Free Software Foundation; either version 2 of the License, or\n(at your option) any later version.\n\nThis program is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the\nGNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License along\nwith this program; if not, write to the Free Software Foundation, Inc.,\n51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.")
		auteurs = ["Ko4la"]
		aboutGTK.set_authors(auteurs)
		aboutGTK.set_logo(pixbuf)
		reponse = aboutGTK.run()
		aboutGTK.destroy()
		

"""
#########################################################################################################################################
#
#                      MAIN
#
#########################################################################################################################################
"""

def main(argv):

	#################################################################################################################################
	# Manage Options
	#########################################################################
	useProgressBar=True							# by default user want a progress bar
	LOGFile='/tmp/masterUbuntu.log'						# by default user don't provide a file to write the log
	OPTFile="mysetup.json"							# by default user don't provide a file to read options
										#
	myMasterOptions=masterOptions(argv)					# init my ugly class to manage CLI options
	args=myMasterOptions.getArgs()						# get "args" according to user's selections
										#
	if args.verbose:							# if verbose
		useProgressBar=False						# progress bar will not be used
										#
	if args.output!=None:							# if output option has been provided
		LOGFile=args.output						# then init LOGFile
										#
	if args.file!=None:							# if file option has been provided
		OPTFile=args.file						# then init OPTFile
	#################################################################################################################################
	# Manage Command
	#########################################################################
	if args.all is True:							#
		myMaster=masterUbuntuCLI(optfile=OPTFile, logfile=LOGFile, useprogressbar=useProgressBar)	#
		myMaster.doTaks()						#
										# Common methodology
	if args.menu is True:							#
		myMaster=masterUbuntuMenu(optfile=OPTFile, logfile=LOGFile, useprogressbar=True)			# Load the class according to the options
		myMaster.doTaks()						#
										#
	if args.gui is True:							#
		myMaster=masterUbuntuGUI(optfile=OPTFile, logfile=LOGFile)
		#print(masterUbuntuGUI.__mro__)

	#################################################################################################################################

if __name__ =='__main__':

	if len(sys.argv)<=1 :							# if no options
		sys.argv.append("--h")						# print usage
	main(sys.argv[1:])							# call main function

"""
#########################################################################################################################################
#
#                      End
#
#########################################################################################################################################
"""
