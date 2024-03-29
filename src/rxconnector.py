"""
    Remote ranorex library for robot framework
    All commands return True if they are executed correctly
"""
#iron python ]%imports
import clr
clr.AddReference('Ranorex.Core')
clr.AddReference('System.Windows.Forms')
import System.Windows.Forms
import Ranorex
#python imports
from System.Collections.Generic import List
from argparse import ArgumentParser
from robotremoteserver import RobotRemoteServer
from os.path import expanduser
import subprocess
import logging
import time
import sys
import os

class RanorexLibrary(object):
    """ Basic implementation of ranorex object calls for
    robot framework
    """
    def __init__(self):
        self.debug = False
        self.model_loaded = False
        self.model = None
        Ranorex.Mouse.DefaultMoveTime = 0
        Ranorex.Keyboard.DefaultKeyPressTime = 20
        #Ranorex.Delay.SpeedFactor = 0.0
        Ranorex.Adapter.DefaultSearchTimeout = 60000
        Ranorex.Adapter.DefaultUseEnsureVisible = True

    def start_debug(self):
        """ Starts to show debug messages on remote connector """
        self.debug = True

    def stop_debug(self):
        """ Stops to show debug messages """
        self.debug = False

    @classmethod
    def __return_type(cls, locator):
        """ Function serves as translator from xpath into
        .net object that is recognized by ranorex.
        Returns supported object type.
        """
        Ranorex.Validate.EnableReport = False
        Ranorex.Adapter.DefaultUseEnsureVisible = True
        supported_types = ['AbbrTag', 'AcronymTag', 'AddressTag', 'AreaTag',
                           'ArticleTag', 'AsideTag', 'ATag', 'AudioTag',
                           'BaseFontTag', 'BaseTag', 'BdoTag', 'BigTag',
                           'BodyTag', 'BrTag', 'BTag', 'Button',
                           'ButtonTag', 'CanvasTag', 'Cell', 'CenterTag',
                           'CheckBox', 'CiteTag', 'CodeTag', 'ColGroupTag',
                           'ColTag', 'Column', 'ComboBox', 'CommandTag',
                           'Container', 'ContextMenu', 'DataListTag', 'DateTime',
                           'DdTag', 'DelTag', 'DetailsTag', 'DfnTag',
                           'DirTag', 'DivTag', 'DlTag', 'EmbedTag', 'EmTag',
                           'FieldSetTag', 'FigureTag', 'FontTag', 'Form', 'FormTag',
                           'Link', 'List', 'ListItem', 'MenuBar',
                           'MenuItem', 'Picture', 'ProgressBar',
                           'RadioButton', 'Row', 'ScrollBar', 'Slider',
                           'StatusBar', 'Table', 'TabPage', 'Text', 'TitleBar',
                           'ToggleButton', 'Tree', 'TreeItem', 'Unknown' ]
                           
        ele = RanorexLibrary.extract_element(locator)
            
        for item in supported_types:
            if ele.lower() == item.lower():
                return item
            elif ele.lower() == '':
                raise AssertionError("No element entered")
                
        log = logging.getLogger("Return type")
        log.debug("Ranorex supports: %s", dir(Ranorex))
            
        raise AssertionError("Element is not supported. Entered element: %s" %ele)
    
    @classmethod
    def extract_element(cls, xpath):
        split_locator = xpath.split('/')
        
        if "[" in split_locator[-1]:
            ele = split_locator[-1].split('[')[0]
            
        elif "[" in split_locator[-2] and "]" in split_locator[-1]:
            # Appears that a forward slash was within a predicate eg. text[@caption='some / randon string']
            # so look for the element in the position -2 rather than -1
            ele = split_locator[-2].split('[')[0]
            
        elif ".." in split_locator[-1]:
            # We found a parent selector in the last element e.g. /row/cell[@text='${ActiveForm}']/..
            # so parent we need is in position -3
            ele = split_locator[-3]
            
        else:
            ele = split_locator[-1]
            
        return ele
    
    def kill_all_browsers(self):
        os.system("TASKKILL /F /IM chrome.exe")
        os.system("TASKKILL /F /IM iexplore.exe")    

    def kill_browser(self, browser):
        """ Kill the browser
        """
        if self.debug:
            log = logging.getLogger("Kill Browser")
            log.debug("browser: %s", browser)
        Ranorex.Host.Local.KillBrowser(browser)
        time.sleep(0.5)

    def close_browser(self, browser):
        """ Close the browser
        """
        if self.debug:
            log = logging.getLogger("Close Browser")
            log.debug("browser: %s", browser)
         
        if browser == "firefox":
            processName = "firefox"
        elif browser == "ie":
            processName = "iexplore"
        elif browser == "chrome":
            processName = "chrome"
        else:
            raise AssertionError("Browser not recognised: %s" %browser)
            
        Ranorex.Host.Local.CloseApplications(processName)
        Ranorex.Delay.Seconds(1)

    def open_browser(self, url, browser, maximize=False):
        """ Opens the browser at a URL
        """
        if self.debug:
            log = logging.getLogger("Open Browser")
            log.debug("url: %s", url)
            log.debug("browser: %s", browser)
        Ranorex.Host.Local.OpenBrowser(url, browser, True, maximize)
        Ranorex.Delay.Seconds(1)

    def check_if_element_exists(self, locator, duration=60000):
        """ Checks if the element exists within the timout (or specified duration)
        """
        if self.debug:
            log = logging.getLogger("Check if element exists")
            log.debug("locator: %s", locator)
            log.debug("duration: %s", duration)
        Ranorex.Validate.Exists(locator, int(duration))
        return True

    def check_if_element_does_not_exist(self, locator, duration=60000):
        """ Checks if the element does not exist within the timout (or specified duration)
        """
        if self.debug:
            log = logging.getLogger("Check if element does not exist")
            log.debug("locator: %s", locator)
            log.debug("duration: %s", duration)
        Ranorex.Validate.NotExists(locator, int(duration))
        return True
        
    def click_element(self, locator, location=None, accessible=True):
        """ Clicks on element identified by locator and location
        """
        if self.debug:
            log = logging.getLogger("Click Element")
            log.debug("Locator: %s", locator)
            log.debug("Location: %s", location)
            log.debug("Accessible Check: %s", accessible)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        ele = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", ele)
            
        if accessible == True:
            if self._wait_until_element_accessible(ele) == False:
                raise AssertionError("Element did not become accessible")

        try:
            if location == None:
                ele.Click()
                Ranorex.Delay.Seconds(1)
                return True
            else:
                if not isinstance(location, basestring):
                    raise AssertionError("Location must be a string")
                    
                if location == "Center":
                   ele.Click(Ranorex.Location.Center)
                elif location == "CenterLeft":
                   ele.Click(Ranorex.Location.CenterLeft)
                elif location == "CenterRight":
                   ele.Click(Ranorex.Location.CenterRight)
                elif location == "LowerCenter":
                   ele.Click(Ranorex.Location.LowerCenter)
                elif location == "LowerLeft":
                   ele.Click(Ranorex.Location.LowerLeft)
                elif location == "LowerRight":
                   ele.Click(Ranorex.Location.LowerRight)
                elif location == "UpperCenter":
                   ele.Click(Ranorex.Location.UpperCenter)
                elif location == "UpperLeft":
                   ele.Click(Ranorex.Location.UpperLeft)
                elif location == "UpperRight":
                   ele.Click(Ranorex.Location.UpperRight)
                else:
                   location = [int(x) for x in location.split(',')]
                   ele.Click(Ranorex.Location(location[0], location[1]))
                   
                Ranorex.Delay.Seconds(1)
                return True
        except Exception as error:
            if self.debug:
                log.error("Failed because of %s", error)
            raise AssertionError(error)

    def _wait_until_element_accessible(self, ele, timeout=60000):
        """ Wait for element to become accessible (enabled & visible)
        """
        if self.debug:
            log = logging.getLogger("Wait Until Element Accessible")
            
        curr_time = 0
        timeout = int(timeout)/1000
        
        while curr_time != timeout:
            enabled = ele.Element.GetAttributeValue("Enabled")
            visible = ele.Element.GetAttributeValue("Visible")

            if self.debug:
                log.debug("Element enabled: %s", enabled)
                log.debug("Element visible: %s", visible)

            if enabled == True and visible == True:
                return True
                
            time.sleep(5)
            curr_time += 5
            
        return False
    
    def check(self, locator):
        """ Check if element is checked. If not it check it.
            Only checkbox and radiobutton are supported.
            Uses Click() method to check it.
        """
        if self.debug:
            log = logging.getLogger("Check")
            log.debug("Locator: %s", locator)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        if element == 'CheckBox' or element == 'RadioButton':
            if self.debug:
                log.debug("Element is radiobutton or checkbox")
            obj = getattr(Ranorex, element)(locator)
            if self.debug:
                log.debug("Application object: %s", obj)
            if not obj.Element.GetAttributeValue('Checked'):
                obj.Element.GetAttributeValue('Checked')
                obj.Click()
                Ranorex.Delay.Seconds(1)
                return True
        else:
            raise AssertionError("Element |%s| is not supported for checking" %
                                 element)

    @classmethod
    def check_if_process_is_running(cls, process_name):
        """ Check if process with desired name is running.
            Returns name of process if running
        """
        proc = subprocess.Popen(['tasklist'], stdout=subprocess.PIPE)
        out = proc.communicate()[0]
        return out.find(process_name) != -1 if out else False

    def clear_text(self, locator):
        """ Clears text from text box. Only element Text is supported.
        """
        if self.debug:
            log = logging.getLogger("Clear Text")
            log.debug("Locator: %s", locator)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        if element != "Text":
            if self.debug:
                log.error("Element is not a text field")
            raise AssertionError("Only element Text is supported!")
        else:
            obj = getattr(Ranorex, element)(locator)
            if self.debug:
                log.debug("Application object: %s", obj)
            obj.PressKeys("{End}{Shift down}{Home}{Shift up}{Delete}")
            return True
        raise AssertionError("Element %s does not exists" % locator)

    def drag(self, locator1, locator2):
        """ Put the mouse button down on the element for dragging
        """
        if self.debug:
            log = logging.getLogger("Drag on Element")
            log.debug("Locator: %s", locator1)
            log.debug("Locator: %s", locator2)
        element1 = self.__return_type(locator1)
        element2 = self.__return_type(locator2)
        if self.debug:
            log.debug("Element: %s", element1)
            log.debug("Element: %s", element2)
        obj1 = getattr(Ranorex, element1)(locator1)
        obj2 = getattr(Ranorex, element2)(locator2)
        if self.debug:
            log.debug("Application object: %s", obj1)
            log.debug("Application object: %s", obj2)
        try:
            obj1.MoveTo()
            Ranorex.Delay.Milliseconds(500)
            Ranorex.Mouse.ButtonDown(System.Windows.Forms.MouseButtons.Left)
            Ranorex.Delay.Milliseconds(500)
            obj2.MoveTo()
            Ranorex.Delay.Milliseconds(500)
            obj2.MoveTo(Ranorex.Location.CenterLeft)
            obj2.MoveTo(Ranorex.Location.Center)
            Ranorex.Mouse.ButtonUp(System.Windows.Forms.MouseButtons.Left)
            #obj.ButtonDown(MouseButtons.Left)
            return True
        except Exception as error:
            raise AssertionError(error)


    def double_click_element(self, locator, location=None, accessible=True):
        """ Doubleclick on element identified by locator. It can click
            on desired location if requested.
        """
        if self.debug:
            log = logging.getLogger("Double Click Element")
            log.debug("Locator: %s", locator)
            log.debug("Location: %s", location)
            log.debug("Accessible Check: %s", accessible)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        ele = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", ele)
            
        if accessible == True:
            if self._wait_until_element_accessible(ele) == False:
                raise AssertionError("Element did not become accessible")
            
        try:
            if location == None:
                ele.DoubleClick()
                Ranorex.Delay.Seconds(1)
                return True
                
            else:
                if not isinstance(location, basestring):
                    raise AssertionError("Location must be a string")
                    
                if location == "CenterRight":
                   ele.DoubleClick(Ranorex.Location.CenterRight)
                else:
                   location = [int(x) for x in location.split(',')]
                   ele.DoubleClick(Ranorex.Location(location[0], location[1]))
                   
                Ranorex.Delay.Seconds(1)
                return True
                
        except Exception as error:
            raise AssertionError(error)

    def get_table(self, locator):
        """ Get content of table without headers

        :param locator: xpath string selecting element on screen
        :return: two dimensional array with content of the table
        """
        element_type = self.__return_type(locator)
        element = getattr(Ranorex, element_type)(locator)
        table = [[cell.Text for cell in row.Cells] for row in element.Rows]

        return table

    def count_list_items(self, locator, childLocator):
        """ Count the items in a list, only works on a list
        """
        if self.debug:
            log = logging.getLogger("Count List Items")
            log.debug("Locator: %s", locator)
            log.debug("Child Locator: %s", childLocator)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        if element != "List":
            if self.debug:
                log.error("Element is not a list field")
            raise AssertionError("Only element List is supported!")
        else:
            obj = getattr(Ranorex, element)(locator)
            if self.debug:
                log.debug("Application object: %s", obj)
            items = obj.Find[Ranorex.ListItem](childLocator)
            if self.debug:
                log.debug("Count: %s", items.Count)
            return items.Count

    def get_element_attribute(self, locator, attribute):
        """ Get specified element attribute.
        """
        if self.debug:
            log = logging.getLogger("Get Element Attribute")
            log.debug("Locator: %s", locator)
            log.debug("Attribute: %s", attribute)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        obj = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", obj)
        found = obj.Element.GetAttributeValue(attribute)
        if self.debug:
            log.debug("Found attribute value is: %s", found)
        return found

    def get_list_items_attribute(self, locator, childLocator, attribute):
        """ Get specified attribute of the list items in a list
        """
        if self.debug:
            log = logging.getLogger("Get List Items Attribute")
            log.debug("Locator: %s", locator)
            log.debug("Child Locator: %s", childLocator)
            log.debug("Attribute: %s", attribute)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        if element != "List":
            if self.debug:
                log.error("Element is not a list field")
            raise AssertionError("Only element List is supported!")
        else:
            obj = getattr(Ranorex, element)(locator)
            if self.debug:
                log.debug("Application object: %s", obj)
                
            items = obj.Find[Ranorex.ListItem](childLocator)
            itemValues = [item.Element.GetAttributeValue(attribute) for item in items]
            if self.debug:
                log.debug("Item Values: %s", itemValues)
            return itemValues

    def input_text(self, locator, text):
        """ input texts into specified locator.
        """
        if self.debug:
            log = logging.getLogger("Input Text")
            log.debug("Locator: %s", locator)
            log.debug("Text to enter: %s", text)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        obj = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", obj)
        obj.PressKeys(text)
        Ranorex.Delay.Seconds(1)
        return True

    def right_click_element(self, locator, location=None):
        """ Rightclick on desired element identified by locator.
        Location of click can be used.
        """
        if self.debug:
            log = logging.getLogger("Right Click Element")
            log.debug("Locator: %s", locator)
            log.debug("Location: %s", location)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        obj = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", obj)
        if location == None:
            obj.Click(System.Windows.Forms.MouseButtons.Right)
            Ranorex.Delay.Seconds(1)
            return True
        else:
            if not isinstance(location, basestring):
                raise AssertionError("Locator must be a string")
            location = [int(x) for x in location.split(',')]
            obj.Click(System.Windows.Forms.MouseButtons.Right,
                      Ranorex.Location(location[0], location[1]))
            Ranorex.Delay.Seconds(1)
            return True

    def run_application(self, app):
        """ Runs local application.
        """
        if self.debug:
            log = logging.getLogger("Run Application")
            log.debug("Application: %s", app)
            log.debug("Working dir: %s", os.getcwd())
        Ranorex.Host.Local.RunApplication(app)
        return True

    def run_application_with_parameters(self, app, params):
        """ Runs local application with parameters.
        """
        if self.debug:
            log = logging.getLogger("Run Application With Parameters")
            log.debug("Application: %s", app)
            log.debug("Parameters: %s", params)
            log.debug("Working dir: %s", os.getcwd())
        Ranorex.Host.Local.RunApplication(app, params)
        return True

    def run_script(self, script_path):
        """ Runs script on remote machine and returns stdout and stderr.
        """
        if self.debug:
            log = logging.getLogger("Run Script")
            log.debug("Script: %s", script_path)
            log.debug("Working dir: %s", os.getcwd())
        process = subprocess.Popen([script_path],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output = process.communicate()
        return {'stdout':output[0], 'stderr':output[1]}

    def run_script_with_parameters(self, script_path, params):
        """ Runs script on remote machine and returns stdout and stderr.
        """
        if self.debug:
            log = logging.getLogger("Run Script With Parameters")
            log.debug("Script: %s", script_path)
            log.debug("Parameters: %s", params)
            log.debug("Working dir: %s", os.getcwd())
        process = subprocess.Popen([script_path, params],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output = process.communicate()
        return {'stdout':output[0], 'stderr':output[1]}

    def scroll(self, locator, amount):
        """ Hover above selected element and scroll positive or negative
        amount of wheel turns

        :param locator: xpath pointing to desired element
        :param amount: int - amount of scrolling
        :return: None
        """
        if self.debug:
            log = logging.getLogger("Scroll")
            log.debug("Locator: %s", locator)
        elem_type = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", elem_type)
        element = getattr(Ranorex, elem_type)(locator)
        if self.debug:
            log.debug("Application object: %s", element)
        
        mouse = Ranorex.Mouse()
        mouse.MoveTo(element.Element)
        mouse.ScrollWheel(int(amount))

    def select_by_index(self, locator, index):
        """ Selects item from combobox according to index.
        """
        if self.debug:
            log = logging.getLogger("Select By Index")
            log.debug("Locator: %s", locator)
            log.debug("Index: %s", index)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        obj = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", obj)
        selected = obj.Element.GetAttributeValue("SelectedItemIndex")
        if self.debug:
            log.debug("Selected item: %s", selected)
        diff = int(selected) - int(index)
        if self.debug:
            log.debug("Diff for keypress: %s", diff)
        if diff >= 0:
            for _ in range(0, diff):
                obj.PressKeys("{up}")
                if self.debug:
                    log.debug("Up")
        elif diff < 0:
            for _ in range(0, abs(diff)):
                obj.PressKeys("{down}")
                if self.debug:
                    log.debug("Down")
        return True

    def set_list_selected_index(self, locator, index):
        """ Set the list selected index
        """
        if self.debug:
            log = logging.getLogger("Set List Selected Index")
            log.debug("Locator: %s", locator)
            log.debug("Index: %s", index)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)

        if element != "List":
            if self.debug:
                log.error("Element is not a list")
            raise AssertionError("Only element List is supported!")
        else:
            try:
                ele = getattr(Ranorex, element)(locator)
                if self.debug:
                    log.debug("Application object: %s", ele)
                    
                """
                What attributes has the element got?
                
                for attr in dir(ele):
                    if hasattr( ele, attr ):
                        log.debug( "ele.%s = %s" % (attr, getattr(ele, attr)))
                """

                ele.Element.SetAttributeValue("selectedIndex", index)
                return True
            except Exception as error:
                if self.debug:
                    log.error("Failed because of %s", error)
                raise AssertionError(error)

    def send_keys(self, locator, key_seq):
        """ Send key combination to specified element.
        Also it gets focus before executing sequence
        seq according to :
        http://msdn.microsoft.com/en-us/library/system.windows.forms.keys.aspx
        """
        if self.debug:
            log = logging.getLogger("Send Keys")
            log.debug("Locator: %s", locator)
            log.debug("Key sequence: %s", key_seq)
        Ranorex.Keyboard.PrepareFocus(locator)
        Ranorex.Keyboard.Press(key_seq)
        time.sleep(0.5)
        return True

    def set_focus(self, locator):
        """ Sets focus on desired location.
        """
        if self.debug:
            log = logging.getLogger("Set Focus")
            log.debug("Locator: %s", locator)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        obj = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", obj)
        obj.Focus()
        Ranorex.Delay.Seconds(1)
        return obj.HasFocus

    def take_screenshot(self, locator):
        """ Takes screenshot and return it as base64.
        """
        if self.debug:
            log = logging.getLogger("Take Screenshot")
            log.debug("Locator: %s", locator)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        obj = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", obj)
        img = obj.CaptureCompressedImage()
        return img.ToBase64String()

    def take_desktop_screenshot(self):
        """ Takes screenshot of the desktop, saves it under name and return it as base64.
        """
        if self.debug:
            log = logging.getLogger("Take Desktop Screenshot")
            
        img = Ranorex.Host.Local.CaptureCompressedImage()
        return img.ToBase64String()

    def get_file_contents(self, name):
        """ Get the file contents
        """
        if self.debug:
            log = logging.getLogger("Get File Contents")
            
        filename = expanduser("~") + name
        if self.debug:
            log.debug("Filename: %s", filename)
        
        with open ( filename, "r") as myfile:
            content = myfile.read()
        return content

    def uncheck(self, locator):
        """ Check if element is checked. If yes it uncheck it
        """
        if self.debug:
            log = logging.getLogger("Uncheck")
            log.debug("Locator: %s", locator)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        if element == 'CheckBox' or element == 'RadioButton':
            obj = getattr(Ranorex, element)(locator)
            if self.debug:
                log.debug("Application object: %s", obj)
            if obj.Element.GetAttributeValue('Checked'):
                if self.debug:
                    log.debug("Object is checked => unchecking")
                obj.Click()
                Ranorex.Delay.Seconds(1)
                return True
        else:
            raise AssertionError("Element |%s| not supported for unchecking"
                                 % element)

    def wait_for_element(self, locator, timeout=60000):
        """ Wait for element becomes on the screen.
        """
        if self.debug:
            log = logging.getLogger("Wait For Element")
            log.debug("Locator: %s", locator)
            log.debug("Timeout: %s", timeout)
        Ranorex.Validate.EnableReport = False
        if Ranorex.Validate.Exists(locator, int(timeout)) is None:
            return True
        raise AssertionError("Element %s does not exists" % locator)

    def wait_for_element_attribute(self, locator, attribute,
                                   expected, timeout=60000):
        """ Wait for element attribute becomes requested value.
        """
        if self.debug:
            log = logging.getLogger("Wait For Element Attribute")
            log.debug("Locator: %s", locator)
            log.debug("Attribute: %s", attribute)
            log.debug("Expected: %s", expected)
            log.debug("Timeout: %s", timeout)
        curr_time = 0
        timeout = int(timeout)/1000
        while curr_time != timeout:
            value = self.get_element_attribute(locator, attribute)
            if str(value) == str(expected):
                return True
            time.sleep(5)
            curr_time += 5
        raise AssertionError("Object at location %s could not be found"
                             % locator)

    def make_visible(self, locator):
        """ Make the element visible
        """
        if self.debug:
            log = logging.getLogger("Make Visible")
            log.debug("Locator: %s", locator)
        element = self.__return_type(locator)
        if self.debug:
            log.debug("Element: %s", element)
        obj = getattr(Ranorex, element)(locator)
        if self.debug:
            log.debug("Application object: %s", obj)
        obj.EnsureVisible()
        Ranorex.Delay.Seconds(1)
        return True

    def wait_for_process_to_start(self, process_name, timeout):
        """ Waits for /timeout/ seconds for process to start.
        """
        if self.debug:
            log = logging.getLogger("Wait For Process To Start")
            log.debug("Process name: %s", process_name)
            log.debug("Timeout: %s", timeout)
        curr_time = 0
        timeout = int(timeout)/1000
        while curr_time <= timeout:
            proc = subprocess.Popen(['tasklist'], stdout=subprocess.PIPE)
            out = proc.communicate()[0]
            res = out.find(process_name) != -1 if out else False
            if res:
                return True
            else:
                curr_time += 5
                time.sleep(5)
        raise AssertionError("Process %s not found within %ss" % (process_name,
                                                                  timeout))

    def kill_process(self, process_name):
        """ Kills process identified by process_name
        """
        if self.debug:
            log = logging.getLogger("Kill Process")
            log.debug("Process name: %s", process_name)
        res = self.check_if_process_is_running(process_name)
        if self.debug:
            log.debug("Process is running: %s", res)
        if not res:
            raise AssertionError("Process %s is not running" % process_name)
        proc = subprocess.Popen(['taskkill', '/im', process_name, '/f'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = proc.communicate()
        if 'SUCCESS' in out[0]:
            if self.debug:
                log.debug("Output of killing: %s", out)
            return True
        else:
            raise AssertionError("Process %s not terminated because of: %s" %
                                 (process_name, out))

def configure_logging():
    logging.basicConfig(
            format="%(asctime)s::[%(name)s.%(levelname)s] %(message)s",
            datefmt="%I:%M:%S %p",
            level='DEBUG')
    logging.StreamHandler(sys.__stdout__)

def main():
    # get configured logger
    logger = logging.getLogger("MAIN")

    # define arguments
    parser = ArgumentParser(prog="rxconnector", description="Remote ranorex library for robot framework")
    parser.add_argument("-i","--ip", required=False, dest="ip", default="0.0.0.0")
    parser.add_argument("-p", "--port", required=False, type=int, dest="port", default=11000)

    # parse arguments
    args = parser.parse_args()

    # run server
    try:
        server = RobotRemoteServer(RanorexLibrary(), args.ip, args.port)
    except KeyboardInterrupt, e:
        log("INFO: Keyboard Iterrupt: stopping server")
        server.stop_remote_server()

if __name__ == '__main__':
    configure_logging()
    main()
    sys.exit(0)
