"""Subclass of gui.py, which is generated by wxFormBuilder."""

import wx
import gui
import urllib2
import cookielib
import webbrowser
import os
import random,string
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from simple_base import TwainBase

# You can either Poll the TWAIN source, or process the scanned image in an
# event callback. The event callback has not been fully tested using GTK.
# Specifically this does not work with Tkinter.
USE_CALLBACK=True
#PROXY='http://proxy8.upd.edu.ph:8080'

#pOpener=register_openers()
#pOpener.add_handler(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))

# Implementing MainFrameBase
class MainFrame( gui.MainFrameBase, TwainBase):
        cookies = cookielib.LWPCookieJar()
        handlers = [
            urllib2.HTTPHandler(),
            urllib2.HTTPSHandler(),
            #urllib2.ProxyHandler({'http': PROXY}),
            urllib2.HTTPCookieProcessor(cookies)
            ]
        opener=register_openers()
        for handler in handlers:
                opener.add_handler(handler)

        params = {}
        filenameList = []

        def log(self,msg):
                if self.debugMode==True: print '****LogMessage: ' + msg

        def fetch(self,uri):
            req = urllib2.Request(uri,headers={'User-Agent' : 'Mozilla/5.0'}) #browser spoofing
            return self.opener.open(req)

        def getCookie(self,cookieName):
            for cookie in self.cookies:
                if cookie.name==cookieName: return cookie

        def setPage(self,page):
                self.pages=page
                self.m_lbCNowpage.ChangeValue(str(page))

        def setMaxPage(self,page):
                self.maxPage=page
                self.m_lbAllpages.ChangeValue(str(page))

        def cleanUp(self):
                fileList=os.listdir('.')
                for x in fileList:
                        if(".bmp" in x): os.remove(x)
        
        def setParams(self,facultyID,facultyName,formTitle,sessid,debug=False):
                self.name=facultyName
                self.m_lbFaculty.ChangeValue(facultyName)
                self.fid=facultyID
                self.maxPage=1
                self.setMaxPage(self.maxPage)
                self.setPage(self.maxPage)
                self.title=formTitle
                self.m_lbDoctype.ChangeValue(formTitle)
                self.m_btChangePage.SetRange(1,self.maxPage)
                self.sessid=sessid
                self.filenameList.append(None)
                self.debugMode=debug
                self.cleanUp()

        def genFilename(self):
                while True:
                        result = ''.join(random.choice(string.ascii_lowercase))
                        result += ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(4)) + ".bmp"
                        if result not in self.filenameList: break
                return result

        def destroyFile(self,page):
                if os.path.isfile(self.filenameList[page-1]):
                        self.params["file_" + str(page)].close()
                        os.remove(self.filenameList[page-1])
        
        def OnClose( self, event ):
                self.cleanUp()
                self.Terminate()
                self.Destroy()
        
        def m_btConnectClick( self, event ):
                self.OpenScanner(self.GetHandle(), ProductName="Simple wxPython Demo", UseCallback=USE_CALLBACK)
        
        def m_btConnectHoverIn( self, event ):
                self.m_statusBar.SetStatusText("Selects a scanner for acquiring images")
        
        def m_btConnectHoverOut( self, event ):
                self.m_statusBar.SetStatusText("")
        
        def m_btScanClick( self, event ):
                self.m_bitmap.GetBitmap().Destroy()

                #If an image is assigned to the page
                if self.filenameList[self.pages-1]!=None:
                        self.log('Found ' + self.filenameList[self.pages-1] + '. Replacing...')
                        self.destroyFile(self.pages)

                #Else
                self.m_bitmap.SetBitmap(wx.NullBitmap)
                self.filenameList[self.pages-1] = self.genFilename()
                self.log('MainFrame: Saving scanned image to ' + self.filenameList[self.pages-1])
                self.AcquireNatively(self.filenameList[self.pages-1])
        
        def m_btScanHoverIn( self, event ):
                self.m_statusBar.SetStatusText("Scans an image")
        
        def m_btScanHoverOut( self, event ):
                self.m_statusBar.SetStatusText("")

        def m_btAddClick( self, event ):
                self.log('MainFrame: Add page')
                self.m_bitmap.SetBitmap(wx.NullBitmap)
                self.setMaxPage(self.maxPage+1)
                self.setPage(self.maxPage)
                self.m_btChangePage.SetRange(1,self.maxPage)
                self.filenameList.append(None)

                self.log(str(self.filenameList))
    
        def m_btAddHoverIn( self, event ):
                self.m_statusBar.SetStatusText("Adds a new page")
    
        def m_btAddHoverOut( self, event ):
                self.m_statusBar.SetStatusText("")

        def m_btRemoveClick( self, event ):
                self.log('MainFrame: Delete page ')
                
                #If one page remains, do not delete!
                if self.maxPage==1:
                        self.log('MainFrame: One page remaining. Will not delete ')
                        return

                #Destroy previous file if an image is assigned
                if self.filenameList[self.pages-1]!=None: self.destroyFile(self.pages)

                #Move images after the deleted page
                for x in range(1,self.maxPage):
                        if x>=self.pages and self.filenameList[x]!=None: self.params.update({"file_" + str(x): open(self.filenameList[x], "rb")})
                if "file_" + str(self.maxPage) in self.params.keys(): del self.params["file_" + str(self.maxPage)]
                del self.filenameList[self.pages-1]

                #If currently at last page
                if self.pages==self.maxPage: self.setPage(self.pages-1)

                #Decrement maxPages
                self.setMaxPage(self.maxPage-1)

                #Reflect changes in navigation buttons
                self.m_btChangePage.SetRange(1,self.maxPage)

                #Refreshes display image
                self.DisplayImage(self.filenameList[self.pages-1])

                self.log(str(self.filenameList))
    
        def m_btRemoveHoverIn( self, event ):
                self.m_statusBar.SetStatusText("Deletes the current page")
    
        def m_btRemoveHoverOut( self, event ):
                self.m_statusBar.SetStatusText("")

        def m_btUploadClick( self, event ):
                res=self.fetch("http://127.0.0.1:8000/upload/")
                XCSRFToken=self.getCookie("csrftoken")

                #"http://httpbin.org/post": Test link. Change to appropriate upload link
                self.params.update({"fid": str(self.fid), "faculty": str(self.name), "filename": str("_"+self.title+"_"), "page": str(self.pages), "sessid": self.sessid, "transaction": self.title})
                datagen, headers = multipart_encode(self.params)
                request=urllib2.Request("http://127.0.0.1:8000/upload/",datagen,headers)
                request.add_header("X-CSRFToken", XCSRFToken.value)
                request.add_header("User-Agent", "Mozilla/5.0") #browser spoofing
                try:
                    print urllib2.urlopen(request).read()
                except urllib2.HTTPError, error:
                    with open("results.html", "w") as f:
                            f.write(error.read())
                    webbrowser.open("results.html")
                        
        def m_btUploadHoverIn( self, event ):
                self.m_statusBar.SetStatusText("Uploads an image")
        
        def m_btUploadHoverOut( self, event ):
                self.m_statusBar.SetStatusText("")

        def m_btChangePageHoverIn( self, event ):
                self.m_statusBar.SetStatusText("Navigates through pages")

        def m_btChangePageHoverOut( self, event ):
                self.m_statusBar.SetStatusText("")
                
        def m_btChangePagePrev( self, event ):
                if self.pages>1:
                        self.setPage(self.pages-1)
                        self.log('MainFrame: Rendering page ' + str(self.pages) + ': ' + str(self.filenameList[self.pages-1]))
                        self.DisplayImage(self.filenameList[self.pages-1])
    
        def m_btChangePageNext( self, event ):
                if self.pages<self.maxPage:
                        self.setPage(self.pages+1)
                        self.log('MainFrame: Rendering page ' + str(self.pages) + ': ' + str(self.filenameList[self.pages-1]))
                        self.DisplayImage(self.filenameList[self.pages-1])

        def m_btExitClick( self, event ):
                self.Close(1)
        
        def m_btExitHoverIn( self, event ):
                self.m_statusBar.SetStatusText("Terminates this program")
        
        def m_btExitHoverOut( self, event ):
                self.m_statusBar.SetStatusText("")

        def DisplayImage(self, ImageFileName):
                if ImageFileName!=None and os.path.isfile(ImageFileName):
                        bmp = wx.Image(ImageFileName, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
                else:
                        bmp = wx.NullBitmap
                self.m_bitmap.SetBitmap(bmp)
                self.m_scrolledWindow.maxWidth = bmp.GetWidth()
                self.m_scrolledWindow.maxHeight = bmp.GetHeight()
                self.m_scrolledWindow.SetScrollbars(20, 20, bmp.GetWidth()/20, bmp.GetHeight()/20)
                self.m_bitmap.Refresh()

        def UpdateFiles(self):
                self.params.update({"file_" + str(self.pages): open(self.filenameList[self.pages-1], "rb")})
                
                
        
        
