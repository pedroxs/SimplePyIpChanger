#!/usr/bin/python2.7

import os
import sys
import subprocess
from PyQt4 import QtCore, QtGui
import socket
import struct
import random
import string
import signal
import hashlib
import atexit
import glob
OT_RSA = '109120132967399429278860960508995541528237502902798129123468757937266291492576446330739696001110603907230888610072655818825358503429057592827629436413108566029093628212635953836686562675849720620786279431090218017681061521755056710823876476444260558147179707119674283982419152118103759076030616683978566631413'

#try:
#    from PyQt4.phonon import Phonon
#except ImportError:
#    app = QtGui.QApplication(sys.argv)
#    QtGui.QMessageBox.critical(None, "Music Player",
#            "Your Qt installation does not have Phonon support.",
#            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Default,
#            QtGui.QMessageBox.NoButton)
#    sys.exit(1)
    
def padStr(string, length):
    strLen = len(string)
    for x in xrange(length-strLen):
        string += "\x00"
        
    return string

def quit(*a):
    for file in glob.iglob('.__*.exe'):
        # Mark the file as non-hidden on windows.
        try:
            subprocess.call(["attrib", "-h", file], shell=False)
        except:
            pass
        try:
            os.remove(file)
        except:
            pass # Access denied. Ow well.
            
    if w.thread:
        w.thread.terminate()
    if w:
        del w.settings
    QtGui.QApplication.quit()
    
class IpChanger(QtGui.QWidget): 
    def __init__(self, *args): 
        QtGui.QWidget.__init__(self, *args) 
 
        # Set title
        self.setWindowTitle("PyIpChanger v1.3")
        
        # create objects
        label = QtGui.QLabel(self.tr("Browse to your Tibia(.exe)."))
        labelHostname = QtGui.QLabel(self.tr("IP Address or Hostname"))
        labelPort = QtGui.QLabel(self.tr("Port"))
        label3 = QtGui.QLabel(self.tr("Messages"))
        credit = QtGui.QLabel(self.tr('Visit <a href="http://vapus.net">VAPus.net</a> for the latest versions. Lisenced under GPL.'))
        
        self.settings = QtCore.QSettings('PyIpChanger', 'Vapus.net')
        self.le = QtGui.QLineEdit()
        self.port = QtGui.QLineEdit()
        self.port.setMaxLength(4)
        self.port.setValidator(QtGui.QIntValidator(20, 0xFFFF, self))
        self.pathToExe = QtGui.QLineEdit()
        self.pathButton = QtGui.QPushButton("Browse for Tibia")
        self.startButton = QtGui.QPushButton("Start!")
        self.te = QtGui.QTextEdit()
        self.te.setFixedHeight(50)
        self.thread = None
        self.windowsClient = False
        
        # Restore settings
        if self.settings.contains("IP"):
            self.le.setText(str(self.settings.value("IP", type=str)))
            
        if self.settings.contains("PATH"):
            self.pathToExe.setText(str(self.settings.value("PATH", type=str)))

        if self.settings.contains("PORT"):
            self.port.setText(str(self.settings.value("PORT", type=str)))
        if not self.port.text():
            # Default port
            self.port.setText("7171")
            
        self.running = False
        
        # layout
        layout = QtGui.QGridLayout(self)
        layout.addWidget(label, 0, 0)
        layout.addWidget(self.pathToExe, 1, 0)
        layout.addWidget(self.pathButton, 1, 1)
        layout.addWidget(labelHostname, 2, 0)
        layout.addWidget(labelPort, 2, 1)
        layout.addWidget(self.le, 3, 0)
        layout.addWidget(self.port, 3, 1)
        layout.addWidget(label3, 4, 0)
        layout.addWidget(self.te, 5, 0)
        layout.addWidget(self.startButton, 5, 1)
        layout.addWidget(credit, 6,0, 1, 3)
        self.setLayout(layout) 

        # create connections
        self.connect(self.le, QtCore.SIGNAL("returnPressed(void)"),
                     self.run)
                     
        self.connect(self.startButton, QtCore.SIGNAL("clicked()"),
                     self.run) 
                     
        self.connect(self.pathButton, QtCore.SIGNAL("clicked()"),
                     self.browse)

        self.musicService = None
        
    def run(self):
        # Allow Hostnames longer than 17 chars by resolving the IP:
        text = str(self.le.text())
        if len(text) > 17:
            try:
                ip = socket.gethostbyname(text)
                if ip != text:
                    self.te.append("'%s' resolved to '%s'" % (text, ip))
                    text = ip
            except:
                self.te.append("'%s' could not be resolved! Is it a valid IP/Hostname?" % (text))
                return
                
        # String object, and the directory
        path = str(self.pathToExe.text())
        directory = os.path.dirname(path)
        
        # Change directory, it will load resources from here.
        os.chdir(directory)

        # This might give a open error if the path is wrong
        try:
            tibia = open(path, "r+b")
        except:
            self.te.append("Error: Unable to open %s" % path)
            return
            
        # This might be NULL if we don't have read access
        data = tibia.read()
        if data == None:
            self.te.append("Error: Unable to read file. Do you have access to it?")
            return

        # Windows or linux client?
        self.windowsClient = ".exe" in path.lower()
        
        # Fix ip
        data = self.fixer(data, text)
        
        if data == None:
            return
            
        # Write temp file.
        tmpFileName = directory + "/" + self.randomFileName()
        tmpFile = open(tmpFileName, "wb")
        tmpFile.write(data)
        
        tmpFile.close()
        
        # Save IP for later
        self.settings.setValue("IP", text)
        
        # Save Port for later
        self.settings.setValue("PORT", str(self.port.text()))
        
        self.settings.sync()
        
        self.te.append("Running...")
        
        # Chmod on Linux
        if sys.platform == "linux2":
            try:
                os.chmod(tmpFileName, 0777)
            except:
                pass
        
        # Mark the file as hidden on Windows
        else:
            try:
                subprocess.call(["attrib", "+h", tmpFileName], shell=False)
            except:
                pass

        # Are we opening a .exe on Linux? Then we can use WINE :)
        if sys.platform == "linux2" and self.windowsClient:
            self._run(["wine", tmpFileName], tmpFileName)
        else:    
            self._run(tmpFileName)
        
    def browse(self):
        # Open file dialog
        filename = QtGui.QFileDialog.getOpenFileName(self, "Open Tibia", self.pathToExe.text())
        
        # Ignore if the user didn't specify a file.
        if not filename:
            return
            
        # Set the field
        self.pathToExe.setText(filename)
        
        # Save for later
        self.settings.setValue("PATH", filename)
        
    def _run(self, command, file=None):
        if file == None:
            file = command
            
        class Thread(QtCore.QThread):
            def run(self):
                self.emit( QtCore.SIGNAL('_running()'))
                
                # Start
                self.p = subprocess.call(self.command, shell=False)
                os.remove(self.file) 
                
                self.emit( QtCore.SIGNAL('_notRunning()'))
       
        # Set thread parameters
        self.thread = Thread()
        self.thread.file = file
        self.thread.command = command
        
        # Bind signals (threadsafe)
        self.connect(self.thread, QtCore.SIGNAL('_running()'), self._running)
        self.connect(self.thread, QtCore.SIGNAL('_notRunning()'), self._notRunning)
        
        # Start thread
        self.thread.start()
#       if not self.musicService or not self.musicService.isRunning():
#           self.musicService = MusicService()
#           self.musicService.server = str(self.le.text())
#           self.musicService.port = int(self.port.text()) + 10000
#           for n in xrange(10):
#               output = Phonon.AudioOutput(Phonon.GameCategory, self) 
#               m_media = Phonon.MediaObject(self) 
#               Phonon.createPath(m_media, output) 
#               self.musicService.players.append(m_media)
#           self.musicService.start()

    def _running(self):
        self.startButton.setDisabled(True)
        self.startButton.setText("Tibia is running...")  
        
    def _notRunning(self):
        self.startButton.setEnabled(True)
        self.startButton.setText("Start!")        
    
    def randomFileName(self):
        return ".__" + (''.join(random.choice(string.letters) for i in xrange(14))) + ".exe"
        
    def fixer(self, data, ip):
        # First RSA key
        base = data.find('1321277432058722840622950990822933849527763264961655079678763')
        if base == -1:
            # Pre 8.61
            base = data.find('124710459426827943004376449897985582167801707960697037164044904')
        
        if base == -1:
            self.te.append("WARNING: Couldn't fix the RSA key!")
        else:    
            # Replace
            data = data[:base] + padStr(OT_RSA, 310) + data[base+310:]
        
        # Then it's the IP
        base = data.find("login01.tibia.com")
        if base == -1:
            # Pre 9.1
            base = data.find("tibia05.cipsoft.com")
            if base == -1:
                # Even older?
                base = data.find("tibia2.cipsoft.com")
                
        if base == -1:
            self.te.append("ERROR: Couldn't fix the IP address!")
            return
        
        
        basePadding = data.find("login02.tibia.com") - data.find("login01.tibia.com") # Required for post-9.44 clients. Atleast on Linux.
        if basePadding < 3:
            basePadding = 20 

        data = data[:base] + (padStr(ip, basePadding) * 10) + data[base+(basePadding * 10):]
        
        # Then the ports:
        # On Linux this is always before the IPs, while on Windows, I believe it's after
        # Either way, we use search :)
        
        base = data.find("\x03\x1c\x00\x00", base-300, base+300)
        try:
            port = int(self.port.text())
            if port and port != 7171:
                if base == -1:
                    self.te.append("ERROR: Couldn't fix the Port!")
                    return
                    
                for x in xrange(10):
                    data = data[:base] + struct.pack("<H", port) + data[base+2:]
                    base += 8
        except ValueError:
            self.te.append("Invalid port!")
        
        # Then make an attempt on the multi client.
        # TODO: Linux clients!
        # Early models
        if self.windowsClient:
            base = data.find('\x84\xC0\x75\x52\x68')
            if base == -1:
                # 8.6+ i think.
                base = data.find('\xC3\x83\xF8\x01\x7E\x0E\x6A')
                if base == -1:
                    # 9.1+
                    base = data.find('\x70\xF4\xFF\xFF\x00\x75\x40')
                    if base != -1:
                        base += 5
                else:
                    base += 4
            else:
                base += 2
           
            if base:
                data = data[:base] + "\xEB" + data[base+1:]
            else:
                self.te.append("WARNING: Couldn't apply MC patch!")

        return data

# Limits:
# loginserver and music server got to be on the same machine.
# Only one player per IP.

# Operations from server.
# 0x00, loading to play cache.
#    string resource
# 0x01 = Play once,
#    string resource
# 0x02 = Play loop
#    string resource
# 0x02 = Stop one
#    string resource
# 0x03 = Stop all
# 0x04 = Drop resource (useful if you do things like dynamically made sounds).
# 0x05 = Resource data.
#    string resource
#    int32 length
#    string length
# 0x06 = Seek
#    string resource
#    uint16 at
# 0x07 = Volume
#    string resource
#    uint8 volume

# Operations from client.
# 0x00, loading ok.
# 0x01, request resource.
#   string resource


    
class MusicService(QtCore.QThread):
    def __init__(self, *a, **k):
        QtCore.QThread.__init__(self, *a, **k)
        self.server = ""
        self.port = 0
        self.files = {}
        self.players = []
        self.aplayers = {}
        self.lastPlayer = None
        self.latest = ""
        self.callback = None
        self.qt = None
    
    def load(self, conn):
        length = struct.unpack("<H", conn.recv(2))[0]
        string = ""
        while len(string) != length:
            string += conn.recv(length - len(string))
        self.latest = string
                
        if not self.latest in self.files:
            path = '._%s_music_%s' % (self.server.replace(".", "_"), hashlib.sha1(self.latest).hexdigest())
            if os.path.isfile(path) and os.path.getsize(path):
                self.files[self.latest] = open(path, "rb")
                for player in self.players:
                    if player.state() != Phonon.PlayingState and player not in self.aplayers.values():
                        player.setCurrentSource(Phonon.MediaSource(self.files[self.latest].name))
                        self.aplayers[self.latest] = player
                        break
                conn.send(chr(0x00))
            else:
                # Send 0x01.
                conn.send(chr(0x01) + struct.pack("<H", len(self.latest)) + self.latest)
        else:
            for player in self.players:
                if player.state() != Phonon.PlayingState and player not in self.aplayers.values():
                    player.setCurrentSource(Phonon.MediaSource(self.files[self.latest].name))
                    self.aplayers[self.latest] = player
                    break
            conn.send(chr(0x00))
                
    def run(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect((self.server, self.port))
        except:
            print ("Can't establish connection to media server %s:%d" % (self.server, self.port))
            return
        
        while True:
            data = conn.recv(1)
            if not len(data):
                continue
            data = ord(data)

            if data == 0x00:
                self.load(conn)
            elif data == 0x01:
                self.load(conn)
                self._play(self.latest)
            elif data == 0x02:
                self.load(conn)
                self._play(self.latest, True)
            elif data == 0x03:
                self.load(conn)
                self._stop(self.latest)
            elif data == 0x04:
                self._stop()
                self.files = {}
                self.latest = ""
            elif data == 0x05:
                length = struct.unpack("<H", conn.recv(2))[0]
                res = ""
                while len(string) != length:
                    res += conn.recv(length - len(string))

                path = '._%s_music_%s' % (self.server.replace(".", "_"), hashlib.sha1(res).hexdigest())
                fileObj = open(path, 'w+b')
                length = struct.unpack("<I", conn.recv(4))[0]

                got = 0
                while got < length:
                    try:
                        string = conn.recv(min(1024, length - got))
                        fileObj.write(string)
                        got += len(string)
                    except:
                        # May raise memory error.
                        import traceback
                        traceback.print_exc()
                        return
                fileObj.flush()

                # Mark the file as hidden on windows.
                try:
                    subprocess.call(["attrib", "+h", path], shell=False)
                except:
                    pass
                self.files[res] = fileObj

                if self.callback:
                    self.callback()
                    self.callback = None
                    
            elif data == 0x06:
                self.load(conn)
                self._seek(self.latest, struct.unpack("<H", conn.recv(2)))[0]
            elif data == 0x07:
                self.load(conn)
                self._volume(self.latest, ord(conn.recv(1)))
                
    def _play(self, res, loop=False):
        if not res in self.files:
            self.callback = lambda: self._play(res, loop)
            return
            
        player = self.aplayers[res]
        
        if loop:
            player.finished.connect(lambda: player.play())
        else:
            def clear():
                print "Clear, ", res
                del self.aplayers[res]
            player.finished.connect(clear)
        print "Playing....", self.files[self.latest].name    
        player.play()
        
        self.lastPlayer = player
        
    def _stop(self, res=None):
        if not res:
            for obj in self.players:
                obj.stop()
            self.aplayers = {}
        else:
            if not res in self.files:
                self.callback = lambda: self._stop(res)
                return
            try:
                self.aplayers[res].stop()
            except:
                pass
                
    def _seek(self, res, seek):
        if not res in self.files:
            self.callback = lambda: self._seek(res, seek)
            return
            
        self.aplayers[res].seek(seek)
        
    def _volume(self, res, volume):
        # Not implanted.
        pass
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("PyIpChanger")
    w = IpChanger()
    signal.signal(signal.SIGINT, quit)
    atexit.register(quit)
    w.show() 
    sys.exit(app.exec_())
