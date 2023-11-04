import os
import platform
import sys
import traceback
from datetime import datetime

import wx
from wx import aui

# try:
#     # According to https://docs.wxpython.org/wx.richtext.1moduleindex.html
#     # richtext needs to be imported before wx.App i.e. wxMeerK40t is instantiated
#     # so, we are doing it here even though we do not refer to it in this file
#     # richtext is used for the Console panel.
#     from wx import richtext
# except ImportError:
#     pass
from meerk40t.gui.consolepanel import Console
from meerk40t.gui.navigationpanels import Navigation
from meerk40t.gui.spoolerpanel import JobSpooler
from meerk40t.gui.wxmscene import SceneWindow
from meerk40t.kernel import CommandSyntaxError, ConsoleFunction, Module, get_safe_path
from meerk40t.kernel.kernel import Job

from ..main import APPLICATION_NAME, APPLICATION_VERSION
from ..tools.kerftest import KerfTool
from ..tools.livinghinges import LivingHingeTool
from .about import About
from .alignment import Alignment
from .bufferview import BufferView
from .devicepanel import DeviceManager
from .executejob import ExecuteJob
from .hersheymanager import (
    HersheyFontManager,
    HersheyFontSelector,
    register_hershey_stuff,
)
from .icons import (
    DARKMODE,
    icons8_emergency_stop_button,
    icons8_gas_industry,
    icons8_home_filled,
    icons8_pause,
)
from .imagesplitter import RenderSplit
from .keymap import Keymap
from .lasertoolpanel import LaserTool
from .materialtest import TemplateTool
from .notes import Notes
from .operation_info import OperationInformation
from .preferences import Preferences
from .propertypanels.blobproperty import BlobPropertyPanel
from .propertypanels.consoleproperty import ConsolePropertiesPanel
from .propertypanels.groupproperties import FilePropertiesPanel, GroupPropertiesPanel
from .propertypanels.hatchproperty import HatchPropertyPanel
from .propertypanels.imageproperty import (
    ImageModificationPanel,
    ImagePropertyPanel,
    ImageVectorisationPanel,
)
from .propertypanels.inputproperty import InputPropertyPanel
from .propertypanels.opbranchproperties import OpBranchPanel
from .propertypanels.operationpropertymain import ParameterPanel
from .propertypanels.outputproperty import OutputPropertyPanel
from .propertypanels.pathproperty import PathPropertyPanel
from .propertypanels.placementproperty import PlacementParameterPanel
from .propertypanels.pointproperty import PointPropertyPanel
from .propertypanels.propertywindow import PropertyWindow
from .propertypanels.rasterwizardpanels import (
    AutoContrastPanel,
    ContrastPanel,
    EdgePanel,
    GammaPanel,
    HalftonePanel,
    SharpenPanel,
    ToneCurvePanel,
)
from .propertypanels.textproperty import TextPropertyPanel
from .propertypanels.waitproperty import WaitPropertyPanel
from .propertypanels.wobbleproperty import WobblePropertyPanel
from .simpleui import SimpleUI
from .simulation import Simulation
from .wordlisteditor import WordlistEditor
from .wxmmain import MeerK40t

"""
Laser software for the Stock-LIHUIYU laserboard.

MeerK40t (pronounced MeerKat) is a built-from-the-ground-up MIT licensed
open-source laser cutting software. See https://github.com/meerk40t/meerk40t
for full details.

wxMeerK40t is the primary gui addon for MeerK40t. It requires wxPython for the interface.
The Transformations work in Windows/OSX/Linux for wxPython 4.0+ (and likely before)

"""

_ = wx.GetTranslation


class ActionPanel(wx.Panel):
    def __init__(
        self,
        *args,
        context=None,
        action=None,
        action_right=None,
        fgcolor=None,
        bgcolor=None,
        icon=None,
        tooltip="",
        **kwds,
    ):
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)

        self.context = context
        self.button_go = wx.Button(self, wx.ID_ANY)
        self.icon = icon
        self.fgcolor = fgcolor
        if bgcolor is not None:
            self.button_go.SetBackgroundColour(bgcolor)
        self.button_go.SetToolTip(tooltip)
        # self.button_go.SetBitmapMargins(0, 0)
        self.action = action
        self.action_right = action_right

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(self.button_go, 1, wx.EXPAND, 0)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.button_go.Bind(wx.EVT_BUTTON, self.on_button_go_click)
        if self.action_right is not None:
            self.button_go.Bind(wx.EVT_RIGHT_DOWN, self.on_button_go_click_right)

        self.button_go.Bind(wx.EVT_SIZE, self.on_button_resize)
        # Initial resize
        self.resize_button()
        self.resize_job = Job(
            process=self.resize_button,
            job_name=f"_resize_actionpanel_{self.Id}",
            interval=0.1,
            times=1,
            run_main=True,
        )

    def on_button_go_click(self, event):
        if self.action is not None:
            self.action()

    def on_button_go_click_right(self, event):
        if self.action_right is not None:
            self.action_right()

    def resize_button(self):
        size = self.button_go.Size
        minsize = min(size[0], size[1]) 
        # Leave some room at the edges, 
        # for every 25 pixel 1 pixel at each side
        room = int(minsize/25) * 2
        best_size = minsize - room
        # At least 20 px high
        best_size = max(best_size, 20)
        border = 2
        bmp = self.icon.GetBitmap(color=self.fgcolor, resize=best_size, buffer=border)
        # s = bmp.Size
        # print(f"Was asking for {best_size}x{best_size}, got {s[0]}x{s[1]}")
        self.button_go.SetBitmap(bmp)
        bmp = self.icon.GetBitmap(resize=best_size, buffer=border)
        self.button_go.SetBitmapFocus(bmp)

    def on_button_resize(self, event):
        self.context.schedule(self.resize_job)
        event.Skip()


class GoPanel(ActionPanel):
    def __init__(self, *args, context=None, **kwds):
        # begin wxGlade: PassesPanel.__init__
        kwds["style"] = kwds.get("style", 0)
        fgcol = context.themes.get("start_fg")
        bgcol = context.themes.get("start_bg")
        ActionPanel.__init__(
            self,
            context=context,
            action=None,
            fgcolor=fgcol,
            bgcolor=bgcol,
            icon=icons8_gas_industry,
            tooltip=_("One Touch: Send Job To Laser "),
            *args,
            **kwds,
        )
        self.click_time = 0
        self.was_mouse = False
        self.button_go.Bind(wx.EVT_BUTTON, self.on_button_go_click)
        self.button_go.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)

    def on_mouse_down(self, event):
        self.was_mouse = True
        event.Skip()

    def on_button_go_click(self, event):
        from time import perf_counter

        this_time = perf_counter()
        if this_time - self.click_time < 0.5:
            return
        if not self.was_mouse:
            channel = self.context.kernel.channel("console")
            channel(
                _(
                    "We intentionally ignored a request to start a job via the keyboard.\n"
                    + "You need to make your intent clear by a deliberate mouse-click"
                )
            )
            return
        if not self.button_go.Enabled:
            return

        self.button_go.Enable(False)
        self.context.kernel.busyinfo.start(msg=_("Processing and sending..."))
        self.context(
            "plan clear copy preprocess validate blob preopt optimize spool\nplan clear\n"
        )
        self.context.kernel.busyinfo.end()
        self.button_go.Enable(True)
        # Reset...
        # Deliberately at the end, as clicks queue...
        self.click_time = perf_counter()
        self.was_mouse = False


def register_panel_go(window, context):
    pane = (
        aui.AuiPaneInfo()
        .Bottom()
        .Caption(_("Go"))
        .MinSize(40, 40)
        .FloatingSize(98, 98)
        .Name("go")
        .CaptionVisible(not context.pane_lock)
        .Hide()
    )
    pane.submenu = "_10_" + _("Laser")
    pane.dock_proportion = 98
    panel = GoPanel(window, wx.ID_ANY, context=context)
    pane.control = panel

    window.on_pane_create(pane)
    context.register("pane/go", pane)


def register_panel_stop(window, context):
    # Define Stop.
    def action():
        context("estop\n")

    pane = (
        aui.AuiPaneInfo()
        .Bottom()
        .Caption(_("Stop"))
        .MinSize(40, 40)
        .FloatingSize(98, 98)
        .Name("stop")
        .Hide()
        .CaptionVisible(not context.pane_lock)
    )
    pane.submenu = "_10_" + _("Laser")
    pane.dock_proportion = 98
    fgcol = context.themes.get("stop_fg")
    bgcol = context.themes.get("stop_bg")
    panel = ActionPanel(
        window,
        wx.ID_ANY,
        context=context,
        action=action,
        fgcolor=fgcol,
        bgcolor=bgcol,
        icon=icons8_emergency_stop_button,
        tooltip=_("Emergency stop/reset the controller."),
    )
    pane.control = panel
    window.on_pane_create(pane)
    context.register("pane/stop", pane)


def register_panel_home(window, context):
    # Define Home.
    def action():
        context("home\n")
        
    def action_right():
        context("physical_home\n")

    pane = (
        aui.AuiPaneInfo()
        .Bottom()
        .Caption(_("Home"))
        .MinSize(40, 40)
        .FloatingSize(98, 98)
        .Name("home")
        .Hide()
        .CaptionVisible(not context.pane_lock)
    )
    pane.submenu = "_10_" + _("Laser")
    pane.dock_proportion = 98
    
    fgcol = None
    bgcol = None
    panel = ActionPanel(
        window,
        wx.ID_ANY,
        context=context,
        action=action,
        action_right=action_right,
        fgcolor=fgcol,
        bgcolor=bgcol,
        icon=icons8_home_filled,
        tooltip=_("Send laser to home position"),
    )
    pane.control = panel
    window.on_pane_create(pane)
    context.register("pane/home", pane)


def register_panel_pause(window, context):
    # Define Pause.
    def action():
        context("pause\n")

    pane = (
        aui.AuiPaneInfo()
        .Caption(_("Pause"))
        .Bottom()
        .MinSize(40, 40)
        .FloatingSize(98, 98)
        .Name("pause")
        .Hide()
        .CaptionVisible(not context.pane_lock)
    )
    pane.submenu = "_10_" + _("Laser")
    pane.dock_proportion = 98
   
    bgcol = context.themes.get("pause_bg")
    fgcol = None
    panel = ActionPanel(
        window,
        wx.ID_ANY,
        context=context,
        action=action,
        fgcolor=fgcol,
        bgcolor=bgcol,
        icon=icons8_pause,
        tooltip=_("Pause/Resume the controller"),
    )
    pane.control = panel
    window.on_pane_create(pane)
    context.register("pane/pause", pane)


supported_languages = (
    ("en", "English", wx.LANGUAGE_ENGLISH),
    ("it", "italiano", wx.LANGUAGE_ITALIAN),
    ("fr", "français", wx.LANGUAGE_FRENCH),
    ("de", "Deutsch", wx.LANGUAGE_GERMAN),
    ("es", "español", wx.LANGUAGE_SPANISH),
    ("zh", "中文", wx.LANGUAGE_CHINESE),
    ("hu", "Magyar", wx.LANGUAGE_HUNGARIAN),
    ("pt_PT", "português", wx.LANGUAGE_PORTUGUESE),
    ("pt_BR", "português brasileiro", wx.LANGUAGE_PORTUGUESE_BRAZILIAN),
    ("ja", "日本", wx.LANGUAGE_JAPANESE),
    ("nl", "Nederlands", wx.LANGUAGE_DUTCH),
)


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class wxMeerK40t(wx.App, Module):
    """
    wxMeerK40t is the wx.App main class and a qualified Module for the MeerK40t kernel.
    Running MeerK40t without the wxMeerK40t gui is both possible and reasonable. This should not change the way the
    underlying code runs. It should just be a series of frames held together with the kernel.
    """

    def __init__(self, context, path):
        wx.App.__init__(self, 0)
        # Is this a Windows machine? If yes:
        # Turn on high-DPI awareness to make sure rendering is sharp on big
        # monitors with font scaling enabled.
        
        high_dpi = context.setting(bool, "high_dpi", True)
        if platform.system() == "Windows" and high_dpi:
            try:
                # https://discuss.wxpython.org/t/support-for-high-dpi-on-windows-10/32925
                from ctypes import OleDLL

                OleDLL("shcore").SetProcessDpiAwareness(1)
            except (AttributeError, ImportError):
                # We're on a non-Windows box.
                pass
            except OSError:
                # Potential access denied.
                pass
        self.supported_languages = supported_languages
        import meerk40t.gui.icons as icons

        self.timer = wx.Timer(self, id=wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, context._kernel.scheduler_main, self.timer)
        context._kernel.scheduler_handles_main_thread_jobs = False
        self.timer.Start(50)
        # try:
        #     res = wx.SystemSettings().GetAppearance().IsDark()
        # except AttributeError:
        #     res = wx.SystemSettings().GetColour(wx.SYS_COLOUR_WINDOW)[0] < 127
        res = wx.SystemSettings().GetColour(wx.SYS_COLOUR_WINDOW)[0] < 127
        icons.DARKMODE = res
        icons.icon_r = 230
        icons.icon_g = 230
        icons.icon_b = 230
        Module.__init__(self, context, path)
        self.locale = None
        self.Bind(wx.EVT_CLOSE, self.on_app_close)
        self.Bind(wx.EVT_QUERY_END_SESSION, self.on_app_close)  # MAC DOCK QUIT.
        self.Bind(wx.EVT_END_SESSION, self.on_app_close)
        self.Bind(wx.EVT_END_PROCESS, self.on_app_close)
        # This catches events when the app is asked to activate by some other process
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)

        # App started add the except hook
        sys.excepthook = handleGUIException

        # Monkey patch for pycharm excepthook override issue. https://youtrack.jetbrains.com/issue/PY-39723
        try:
            import importlib

            pydevd = importlib.import_module("_pydevd_bundle.pydevd_breakpoints")
        except ImportError:
            pass
        else:
            pydevd._fallback_excepthook = sys.excepthook

        # Set the delay after which the tooltip disappears or how long a tooltip remains visible.
        self.context.setting(int, "tooltip_autopop", 10000)
        # Set the delay after which the tooltip appears.
        self.context.setting(int, "tooltip_delay", 100)
        autopop_ms = self.context.tooltip_autopop
        delay_ms = self.context.tooltip_delay
        wx.ToolTip.SetAutoPop(autopop_ms)
        wx.ToolTip.SetDelay(delay_ms)
        wx.ToolTip.SetReshow(0)

    def on_app_close(self, event=None):
        try:
            if self.context is not None:
                self.context("quit\n")
        except AttributeError:
            pass

    def OnInit(self):
        return True

    def InitLocale(self):
        import sys

        if sys.platform.startswith("win") and sys.version_info > (3, 8):
            # This hack is needed to deal with  a new Python 3.8 behaviour to
            # set the locale at runtime. wxpython assumes it can do with the
            # locale objects whatever it wants, so we need to bring it back to
            # a defined default

            import locale

            locale.setlocale(locale.LC_ALL, "C")

    def BringWindowToFront(self):
        try:  # it's possible for this event to come when the frame is closed
            self.GetTopWindow().Raise()
        except Exception:
            pass

    def OnActivate(self, event):
        # if this is an activate event, rather than something else, like iconize.
        if event.GetActive():
            self.BringWindowToFront()
        event.Skip()

    def MacReopenApp(self):
        """Called when the doc icon is clicked, and ???"""
        self.BringWindowToFront()

    def MacNewFile(self):
        try:
            if self.context is not None:
                self.context.elements.clear_all()
        except AttributeError:
            pass

    def MacPrintFile(self, file_path):
        pass

    def MacOpenFile(self, filename):
        try:
            if self.context is not None:
                self.context.elements.load(os.path.realpath(filename))
        except AttributeError:
            pass

    def MacOpenFiles(self, filenames):
        try:
            if self.context is not None:
                for filename in filenames:
                    self.context.elements.load(os.path.realpath(filename))
        except AttributeError:
            pass

    @staticmethod
    def sub_register(kernel):
        #################
        # WINDOW COMMANDS
        #################

        @kernel.console_option(
            "path",
            "p",
            type=str,
            default="/",
            help=_("Context Path at which to open the window"),
        )
        @kernel.console_command(
            "window", output_type="window", help=_("Base window command")
        )
        def window_base(channel, _, path=None, remainder=None, **kwargs):
            """
            Opens a MeerK40t window or provides information. This command is restricted to use with the wxMeerK40t gui.
            This also allows use of a -p flag that sets the context path for this window to operate at. This should
            often be restricted to where the windows are typically opened since their function and settings usually
            depend on the context used. Windows often cannot open multiple copies of the same window at the same context
            The default root path is "/". Eg. "window -p / open Preferences"
            """
            context = kernel.root
            if path is None:
                path = context
            else:
                path = kernel.get_context(path)

            if remainder is None:
                channel(
                    _("Loaded Windows in Context {name}:").format(
                        name=str(context.path)
                    )
                )
                for i, name in enumerate(context.opened):
                    if not name.startswith("window"):
                        continue
                    module = context.opened[name]
                    channel(
                        _("{index}: {name} as type of {type}").format(
                            index=i + 1, name=name, type=type(module)
                        )
                    )

                channel("----------")
                if path is context:
                    return "window", path
                channel(_("Loaded Windows in Path {path}:").format(path=str(path.path)))
                for i, name in enumerate(path.opened):
                    if not name.startswith("window"):
                        continue
                    module = path.opened[name]
                    channel(
                        _("{index}: {name} as type of {type}").format(
                            index=i + 1, name=name, type=type(module)
                        )
                    )
                channel("----------")
            return "window", path

        @kernel.console_command(
            "list",
            input_type="window",
            output_type="window",
            help=_("List available windows."),
        )
        def window_list(channel, _, data, **kwargs):
            channel(_("----------"))
            channel(_("Windows Registered:"))
            context = kernel.root
            for i, name in enumerate(context.match("window")):
                name = name[7:]
                channel(f"{i + 1}: {name}")
            return "window", data

        @kernel.console_command(
            "displays",
            input_type="window",
            output_type="window",
            help=_("Give display info for the current opened windows"),
        )
        def displays(channel, _, data, **kwargs):
            for idx in range(wx.Display.GetCount()):
                d = wx.Display(idx)
                channel(f"{idx} Primary: {d.IsPrimary()} {d.GetGeometry()}")
            channel(_("----------"))
            path = data
            for opened in path.opened:
                if opened.startswith("window/"):
                    window = path.opened[opened]
                    display = wx.Display.GetFromWindow(window)
                    if display == wx.NOT_FOUND:
                        display = "Display Not Found"
                    channel(
                        f"Window {opened} with bounds {window.GetRect()} is located on display: {display})"
                    )
            return "window", data

        @kernel.console_option(
            "multi",
            "m",
            type=int,
            help=_("Multi window flag for launching multiple copies of this window."),
        )
        @kernel.console_argument("window", type=str, help=_("window to be opened"))
        @kernel.console_command(
            ("open", "toggle"),
            input_type="window",
            help=_("open/toggle the supplied window"),
        )
        def window_open(
            command, channel, _, data, multi=None, window=None, args=(), **kwargs
        ):
            context = kernel.root
            path = data
            try:
                parent = context.gui
            except AttributeError:
                parent = None
            window_uri = f"window/{window}"
            window_class = context.lookup(window_uri)
            if isinstance(window_class, str):
                window_uri = window_class
                window_class = context.lookup(window_uri)

            new_path = context.lookup(f"winpath/{window}")
            if new_path:
                path = new_path
            else:
                path = context

            window_name = f"{window_uri}:{multi}" if multi is not None else window_uri

            def window_open(*a, **k):
                path.open_as(window_uri, window_name, parent, *args)
                channel(_("Window opened: {window}").format(window=window))

            def window_close(*a, **k):
                path.close(window_name, *args)
                channel(_("Window closed: {window}").format(window=window))

            if command == "open":
                if path.lookup(window_uri) is not None:
                    if wx.IsMainThread():
                        window_open(None)
                    else:
                        wx.CallAfter(window_open, None)
                    # kernel.run_later(window_open, None)
                else:
                    channel(_("No such window as {window}").format(window=window))
                    raise CommandSyntaxError
            else:  # Toggle.
                if window_class is not None:
                    if window_name in path.opened:
                        if wx.IsMainThread():
                            window_close(None)
                        else:
                            wx.CallAfter(window_close, None)
                        # kernel.run_later(window_close, None)
                    else:
                        if wx.IsMainThread():
                            window_open(None)
                        else:
                            wx.CallAfter(window_open, None)
                        # kernel.run_later(window_open, None)
                else:
                    channel(_("No such window as {name}").format(name=window))
                    raise CommandSyntaxError

        @kernel.console_argument("window", type=str, help=_("window to be closed"))
        @kernel.console_command(
            "close",
            input_type="window",
            output_type="window",
            help=_("close the supplied window"),
        )
        def window_close(channel, _, data, window=None, args=(), **kwargs):
            path = data
            context = kernel.root
            try:
                parent = context.gui if hasattr(context, "gui") else None
                if wx.IsMainThread():
                    path.close(f"window/{window}", parent, *args)
                else:
                    wx.CallAfter(path.close(f"window/{window}", parent, *args), None)
                channel(_("Window closed."))
            except (KeyError, ValueError):
                channel(_("No such window as {window}").format(window=window))
            except IndexError:
                raise CommandSyntaxError

        @kernel.console_argument("window", type=str, help=_("window to be reset"))
        @kernel.console_command(
            "reset",
            input_type="window",
            output_type="window",
            help=_("reset the supplied window, or '*' for all windows"),
        )
        def window_reset(channel, _, data, window=None, **kwargs):
            for section in list(kernel.section_startswith("window/")):
                kernel.clear_persistent(section)
                try:
                    del kernel.contexts[section]
                except KeyError:
                    pass  # No open context for that window, nothing will save out.

        @kernel.console_command("refresh", help=_("Refresh the main wxMeerK40 window"))
        def scene_refresh(command, channel, _, **kwargs):
            context = kernel.root
            context.signal("refresh_scene", "Scene")
            context.signal("rebuild_tree")
            channel(_("Refreshed."))

        @kernel.console_command("tooltips_enable", hidden=True)
        def tooltip_enable(command, channel, _, **kwargs):
            context = kernel.root
            context.setting(bool, "disable_tool_tips", False)
            context.disable_tool_tips = False
            wx.ToolTip.Enable(not context.disable_tool_tips)

        @kernel.console_command("tooltips_disable", hidden=True)
        def tooltip_disable(command, channel, _, **kwargs):
            context = kernel.root
            context.setting(bool, "disable_tool_tips", False)
            context.disable_tool_tips = True
            wx.ToolTip.Enable(not context.disable_tool_tips)

    def module_open(self, *args, **kwargs):
        context = self.context
        kernel = context.kernel

        try:  # pyinstaller internal location
            # pylint: disable=no-member
            _resource_path = os.path.join(sys._MEIPASS, "locale")
            wx.Locale.AddCatalogLookupPathPrefix(_resource_path)
        except Exception:
            pass

        try:  # Mac py2app resource
            _resource_path = os.path.join(os.environ["RESOURCEPATH"], "locale")
            wx.Locale.AddCatalogLookupPathPrefix(_resource_path)
        except Exception:
            pass

        wx.Locale.AddCatalogLookupPathPrefix("locale")

        # Default Locale, prepended. Check this first.
        basepath = os.path.abspath(os.path.dirname(sys.argv[0]))
        localedir = os.path.join(basepath, "locale")
        wx.Locale.AddCatalogLookupPathPrefix(localedir)

        kernel.translation = wx.GetTranslation

        context.app = self  # Registers self as kernel.app

        context.setting(int, "language", None)
        language = context.language
        from meerk40t.gui.help_assets.help_assets import asset

        def get_asset(asset_name):
            return asset(context, asset_name)

        context.asset = get_asset
        if language is not None and language != 0:
            self.update_language(language)

        kernel.register("window/MeerK40t", MeerK40t)

        kernel.register("window/Properties", PropertyWindow)
        kernel.register("property/RasterOpNode/OpMain", ParameterPanel)
        kernel.register("property/CutOpNode/OpMain", ParameterPanel)
        kernel.register("property/EngraveOpNode/OpMain", ParameterPanel)
        kernel.register("property/ImageOpNode/OpMain", ParameterPanel)
        kernel.register("property/DotsOpNode/OpMain", ParameterPanel)
        kernel.register("property/PlaceCurrentNode/OpMain", PlacementParameterPanel)
        kernel.register("property/PlacePointNode/OpMain", PlacementParameterPanel)

        kernel.register("property/ConsoleOperation/Property", ConsolePropertiesPanel)
        kernel.register("property/FileNode/Property", FilePropertiesPanel)
        kernel.register("property/GroupNode/Property", GroupPropertiesPanel)
        kernel.register("property/EllipseNode/PathProperty", PathPropertyPanel)
        kernel.register("property/PathNode/PathProperty", PathPropertyPanel)
        kernel.register("property/LineNode/PathProperty", PathPropertyPanel)
        kernel.register("property/PolylineNode/PathProperty", PathPropertyPanel)
        kernel.register("property/RectNode/PathProperty", PathPropertyPanel)
        kernel.register("property/HatchEffectNode/HatchProperty", HatchPropertyPanel)
        kernel.register("property/WobbleEffectNode/WobbleProperty", WobblePropertyPanel)
        kernel.register("property/PointNode/PointProperty", PointPropertyPanel)
        kernel.register("property/TextNode/TextProperty", TextPropertyPanel)
        kernel.register("property/BlobNode/BlobProperty", BlobPropertyPanel)
        kernel.register("property/WaitOperation/WaitProperty", WaitPropertyPanel)
        kernel.register("property/InputOperation/InputProperty", InputPropertyPanel)
        kernel.register("property/BranchOperationsNode/LoopProperty", OpBranchPanel)
        kernel.register("property/OutputOperation/OutputProperty", OutputPropertyPanel)
        kernel.register("property/ImageNode/ImageProperty", ImagePropertyPanel)

        kernel.register("property/ImageNode/SharpenProperty", SharpenPanel)
        kernel.register("property/ImageNode/ContrastProperty", ContrastPanel)
        kernel.register("property/ImageNode/ToneCurveProperty", ToneCurvePanel)
        kernel.register("property/ImageNode/HalftoneProperty", HalftonePanel)
        kernel.register("property/ImageNode/GammaProperty", GammaPanel)
        kernel.register("property/ImageNode/EdgeProperty", EdgePanel)
        kernel.register("property/ImageNode/AutoContrastProperty", AutoContrastPanel)

        kernel.register("property/ImageNode/ImageModification", ImageModificationPanel)
        kernel.register(
            "property/ImageNode/ImageVectorisation", ImageVectorisationPanel
        )

        kernel.register("window/Console", Console)
        kernel.register("window/Preferences", Preferences)
        kernel.register("window/About", About)
        kernel.register("window/Keymap", Keymap)
        kernel.register("window/Wordlist", WordlistEditor)
        kernel.register("window/Navigation", Navigation)
        kernel.register("window/Notes", Notes)
        kernel.register("window/JobSpooler", JobSpooler)
        kernel.register("window/Simulation", Simulation)
        kernel.register("window/ExecuteJob", ExecuteJob)
        kernel.register("window/BufferView", BufferView)
        kernel.register("window/Scene", SceneWindow)
        kernel.register("window/DeviceManager", DeviceManager)
        kernel.register("window/Alignment", Alignment)
        kernel.register("window/HersheyFontManager", HersheyFontManager)
        kernel.register("window/HersheyFontSelector", HersheyFontSelector)
        kernel.register("window/SplitImage", RenderSplit)
        kernel.register("window/OperationInfo", OperationInformation)
        kernel.register("window/Lasertool", LaserTool)
        kernel.register("window/Templatetool", TemplateTool)
        kernel.register("window/Hingetool", LivingHingeTool)
        kernel.register("window/Kerftest", KerfTool)
        kernel.register("window/SimpleUI", SimpleUI)
        # Hershey Manager stuff
        register_hershey_stuff(kernel)

        from meerk40t.gui.wxmribbon import register_panel_ribbon

        kernel.register("wxpane/Ribbon", register_panel_ribbon)

        from meerk40t.gui.wxmscene import register_panel_scene

        kernel.register("wxpane/ScenePane", register_panel_scene)

        from meerk40t.gui.wxmtree import register_panel_tree

        kernel.register("wxpane/Tree", register_panel_tree)

        from meerk40t.gui.laserpanel import register_panel_laser

        kernel.register("wxpane/LaserPanel", register_panel_laser)

        from meerk40t.gui.position import register_panel_position

        kernel.register("wxpane/Position", register_panel_position)

        from meerk40t.gui.opassignment import register_panel_operation_assign

        kernel.register("wxpane/opassign", register_panel_operation_assign)

        from meerk40t.gui.snapoptions import register_panel_snapoptions

        kernel.register("wxpane/Snap", register_panel_snapoptions)

        from meerk40t.gui.wordlisteditor import register_panel_wordlist

        kernel.register("wxpane/wordlist", register_panel_wordlist)

        # from meerk40t.gui.auitoolbars import register_toolbars

        # kernel.register("wxpane/Toolbars", register_toolbars)

        kernel.register("wxpane/Go", register_panel_go)
        kernel.register("wxpane/Stop", register_panel_stop)
        kernel.register("wxpane/Home", register_panel_home)
        kernel.register("wxpane/Pause", register_panel_pause)

        from meerk40t.gui.dialogoptions import DialogOptions

        kernel.register("dialog/options", DialogOptions)

        context = kernel.root

        context.setting(bool, "developer_mode", False)
        context.setting(bool, "debug_mode", False)
        if context.debug_mode:
            from meerk40t.gui.mkdebug import (
                register_panel_color,
                register_panel_debugger,
                register_panel_icon
            )

            kernel.register("wxpane/debug_tree", register_panel_debugger)
            kernel.register("wxpane/debug_color", register_panel_color)
            kernel.register("wxpane/debug_icons", register_panel_icon)

        @context.console_argument("sure", type=str, help="Are you sure? 'yes'?")
        @context.console_command("nuke_settings", hidden=True)
        def nuke_settings(command, channel, _, sure=None, **kwargs):
            if sure == "yes":
                kernel = self.context.kernel
                kernel.delete_all_persistent()
                kernel.shutdown()
            else:
                channel(
                    'Argument "sure" is required. Requires typing: "nuke_settings yes"'
                )

    def update_language(self, lang):
        """
        Update language to the requested language.
        """
        context = self.context
        try:
            language_code, language_name, language_index = supported_languages[lang]
        except (IndexError, ValueError):
            return
        context.language = lang

        if self.locale:
            assert sys.getrefcount(self.locale) <= 2
            del self.locale
        self.locale = wx.Locale(language_index)
        # wxWidgets is broken. IsOk()==false and pops up error dialog, but it translates fine!
        if self.locale.IsOk() or platform.system() == "Linux":
            self.locale.AddCatalog("meerk40t")
        else:
            self.locale = None
        context.signal("language", (lang, language_code, language_name, language_index))


# end of class MeerK40tGui

MEERK40T_HOST = "dev.meerk40t.com"


def send_file_to_developers(filename):
    """
    Loads a file to send data to the developers.

    @param filename: file to send
    @return:
    """
    try:
        with open(filename) as f:
            data = f.read()
    except:
        return  # There is no file, there is no data.
    send_data_to_developers(filename, data)


def send_data_to_developers(filename, data):
    """
    Sends crash log to a server using rfc1341 7.2 The multipart Content-Type
    https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html

    @param filename: filename to use when sending file
    @param data: data to send
    @return:
    """
    import socket

    host = MEERK40T_HOST  # Replace with the actual host
    port = 80  # Replace with the actual port

    # Construct the HTTP request
    boundary = "----------------meerk40t-boundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/plain\r\n"
        "\r\n"
        f"{data}\r\n"
        f"--{boundary}--\r\n"
    )

    headers = (
        f"POST /upload HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "User-Agent: meerk40t/1.0.0\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
    )

    try:
        # Create a socket connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))

            # Send the request
            request = f"{headers}{body}"
            client_socket.sendall(request.encode())

            # Receive and print the response
            response = client_socket.recv(4096)
            response = response.decode("utf-8")
    except Exception:
        response = ""

    response_lines = response.split("\n")
    http_code = response_lines[0]

    print(response)

    if http_code.startswith("HTTP/1.1 200 OK"):
        message = response_lines[-1]
        dlg = wx.MessageDialog(
            None,
            _("We got your message. Thank you for helping\n\n") + message,
            _("Thanks"),
            wx.OK,
        )
        dlg.ShowModal()
        dlg.Destroy()
    else:
        # print(response)
        MEERK40T_ISSUES = "https://github.com/meerk40t/meerk40t/issues"
        dlg = wx.MessageDialog(
            None,
            _(
                "We're sorry, that didn't work. Raise an issue on the github please.\n\n "
                "The log file will be in your working directory.\n"
            )
            + MEERK40T_ISSUES
            + "\n\n"
            + str(http_code),
            _("Thanks"),
            wx.OK,
        )
        dlg.ShowModal()
        dlg.Destroy()


def handleGUIException(exc_type, exc_value, exc_traceback):
    """
    Handler for errors. Save error to a file, and create dialog.

    @param exc_type:
    @param exc_value:
    @param exc_traceback:
    @return:
    """

    def _extended_dialog(caption, header, body):
        dlg = wx.Dialog(
            None,
            wx.ID_ANY,
            title=caption,
            size=wx.DefaultSize,
            pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE,
        )
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(dlg, wx.ID_ANY, header)
        sizer.Add(label, 1, wx.EXPAND, 0)
        info = wx.TextCtrl(dlg, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY)
        info.SetValue(body)
        sizer.Add(info, 5, wx.EXPAND, 0)
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(dlg, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btn = wx.Button(dlg, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.EXPAND, 0)
        dlg.SetSizer(sizer)
        sizer.Fit(dlg)
        dlg.CenterOnScreen()
        return dlg

    def _variable_summary(vars, indent: int = 0):
        info = ""
        for name, value in vars.items():
            label = f'{" " * indent}{name} : '
            total_indent = len(label)
            formatted = str(value)
            formatted = formatted.replace("\n", "\n" + " " * total_indent)
            info += f"{label}{formatted}\n"
        return info

    wxversion = "wx"
    try:
        wxversion = wx.version()
    except:
        pass

    error_log = (
        f"MeerK40t crash log. Version: {APPLICATION_VERSION} on {platform.system()}: "
        f"Python {platform.python_version()}: {platform.machine()} - wxPython: {wxversion}\n"
    )
    error_log += "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    variable_info = ""
    try:
        frame = exc_traceback.tb_frame
        variable_info = "\nLocal variables:\n"
        variable_info += _variable_summary(frame.f_locals)
    except Exception:
        pass
    try:
        filename = f"MeerK40t-{datetime.now():%Y-%m-%d_%H_%M_%S}.txt"
    except Exception:  # I already crashed once, if there's another here just ignore it.
        filename = "MeerK40t-Crash.txt"

    try:
        try:
            with open(filename, "w", encoding="utf8") as file:
                file.write(error_log)
                if variable_info:
                    file.write(variable_info)
                print(error_log)
        except PermissionError:
            filename = get_safe_path(APPLICATION_NAME).joinpath(filename)
            with open(filename, "w", encoding="utf8") as file:
                file.write(error_log)
                if variable_info:
                    file.write(variable_info)
                print(error_log)
    except Exception:
        # I already crashed once, if there's another here just ignore it.
        pass

    # Ask to send file.
    message = _(
        """The bad news is that MeerK40t encountered a crash, and the developers apologise for this bug!

The good news is that you can help us fix this bug by anonymously sending us the crash details."""
    )
    message += "\n" + _(
        "Only the crash details below are sent. No data from your MeerK40t project is sent. No "
        + "personal information is sent either.\n"
        + "Send the following data to the MeerK40t team?"
    )
    caption = _("Crash Detected! Send Log?")
    data = error_log
    if variable_info:
        data += "\n" + variable_info
    try:
        dlg = _extended_dialog(caption, message, data)
        answer = dlg.ShowModal()
        dlg.Destroy()
    except Exception:
        answer = wx.ID_NO
    if answer in (wx.YES, wx.ID_YES, wx.ID_OK):
        send_data_to_developers(filename, data)
