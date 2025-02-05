import wx
import asyncio
import threading
import os
from config_manager import IniConfigManager
from src.chat_api import OllamaChatAPI
from chat_controller import ChatController
from src.ui_components import ServerPanel, ChatPanel, TaskBarIcon
from constant import CONFIG_FILE, DEFAULT_SERVER, DEFAULT_TIMEOUT


class ChatFrame(wx.Frame):
    """主窗口"""

    def __init__(self):
        super().__init__(parent=None, title="Ollama AI", size=(800, 800))
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.SetMinSize((800, 600))  # 设置最小窗口尺寸

        # 设置图标
        icon_path = os.path.join(os.path.dirname(__file__), "../icon.png")
        if os.path.exists(icon_path):
            self.icon = wx.Icon(icon_path)
            self.SetIcon(self.icon)
        else:
            print(f"图标文件不存在: {icon_path}")

        # 创建任务栏图标
        self.taskbar_icon = TaskBarIcon(self)

        # 绑定最小化事件
        self.Bind(wx.EVT_ICONIZE, self.on_minimize)

        try:
            # 初始化事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # 初始化控制器
            config_manager = IniConfigManager(CONFIG_FILE, DEFAULT_SERVER, DEFAULT_TIMEOUT)
            chat_api = OllamaChatAPI(DEFAULT_SERVER, DEFAULT_TIMEOUT)
            self.controller = ChatController(config_manager, chat_api)

            # 先加载配置
            self.controller.initialize()

            # 后初始化UI
            self.init_ui()
            self.Center()

            # 绑定关闭事件
            self.Bind(wx.EVT_CLOSE, self.on_close)
        except Exception as e:
            wx.MessageBox(f"初始化失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            raise

    def init_ui(self):
        """初始化UI"""
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 服务器连接面板
        self.server_panel = ServerPanel(main_panel, self.on_connect, self.on_favorite)

        # 聊天面板
        self.chat_panel = ChatPanel(main_panel, self.on_send)

        # 布局
        main_sizer.Add(self.server_panel, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.chat_panel, 1, wx.ALL | wx.EXPAND, 5)
        main_panel.SetSizer(main_sizer)

        # 更新UI状态
        self.update_favorites()

    def on_connect(self, server_url: str):
        """处理连接/断开事件"""
        if self.controller.is_connected:
            self.disconnect()
        else:
            self.connect(server_url)

    def connect(self, server_url: str):
        """连接到服务器"""

        def on_connect_complete(future):
            try:
                models = future.result()
                wx.CallAfter(self.on_connect_success, models)
            except Exception as e:
                wx.CallAfter(self.on_connect_error, str(e))

        self.server_panel.set_connecting_state()
        future = asyncio.run_coroutine_threadsafe(self.controller.connect(server_url), self.loop)
        future.add_done_callback(on_connect_complete)

    def disconnect(self):
        """断开连接"""

        def on_disconnect_complete(future):
            try:
                future.result()
                wx.CallAfter(self.on_disconnect_success)
            except Exception as e:
                wx.CallAfter(self.on_disconnect_error, str(e))

        future = asyncio.run_coroutine_threadsafe(self.controller.disconnect(), self.loop)
        future.add_done_callback(on_disconnect_complete)

    def on_connect_success(self, models):
        """连接成功处理"""
        self.server_panel.update_models(models)
        if models:
            self.controller.set_current_model(models[0]["name"])
            self.server_panel.set_connection_state(True)
            self.chat_panel.set_send_state(True)
            wx.MessageBox("连接成功！", "提示", wx.OK | wx.ICON_INFORMATION)
        else:
            self.on_connect_error("没有可用的模型")

    def on_connect_error(self, error_msg: str):
        """连接失败处理"""
        self.server_panel.set_connection_state(False)
        self.chat_panel.set_send_state(False)
        wx.MessageBox(f"连接失败：{error_msg}", "错误", wx.OK | wx.ICON_ERROR)

    def on_disconnect_success(self):
        """断开连接成功处理"""
        self.server_panel.set_connection_state(False)
        self.chat_panel.set_send_state(False)
        self.chat_panel.update_chat_display([])

    def on_disconnect_error(self, error_msg: str):
        """断开连接失败处理"""
        wx.MessageBox(f"断开连接失败：{error_msg}", "错误", wx.OK | wx.ICON_ERROR)

    def update_favorites(self):
        """更新收藏列表"""
        favorites = self.controller.get_favorite_servers()
        self.server_panel.update_favorites(favorites)

    def on_favorite(self, server_url: str):
        """处理收藏/取消收藏"""
        is_favorite = self.controller.toggle_favorite(server_url)
        self.update_favorites()

    def on_send(self, message: str):
        """处理发送消息"""

        def on_send_complete(future):
            try:
                future.result()
                wx.CallAfter(self.on_send_success)
            except Exception as e:
                wx.CallAfter(self.on_send_error, str(e))

        self.chat_panel.clear_input()
        self.chat_panel.set_send_state(False, True)

        future = asyncio.run_coroutine_threadsafe(self.controller.send_message(message), self.loop)
        future.add_done_callback(on_send_complete)

    def on_send_success(self):
        """发送成功处理"""
        self.chat_panel.set_send_state(True)
        self.chat_panel.update_chat_display(self.controller.get_messages())

    def on_send_error(self, error_msg: str):
        """发送失败处理"""
        self.chat_panel.set_send_state(True)
        wx.MessageBox(f"发送失败：{error_msg}", "错误", wx.OK | wx.ICON_ERROR)

    def on_minimize(self, event):
        """处理最小化事件"""
        if event.Iconized():
            self.Hide()
        event.Skip()

    def on_close(self, event):
        """关闭窗口处理"""
        # 检查是否有默认行为
        action = self.controller.config_manager.get_close_action()
        if action != "ask":
            if action == "exit":
                self._do_exit()
                event.Skip()
            else:  # minimize
                self.Hide()
                event.Veto()
            return

        # 创建自定义对话框
        dlg = wx.Dialog(self, title="关闭选项", size=(300, 150))
        dlg.SetBackgroundColour(wx.Colour(240, 240, 240))

        sizer = wx.BoxSizer(wx.VERTICAL)

        # 将对话框居中显示
        dlg.CenterOnParent()

        # 提示文本
        label = wx.StaticText(dlg, label="您想要退出程序还是最小化到系统托盘？")
        sizer.Add(label, 0, wx.ALL | wx.CENTER, 10)

        # 复选框
        checkbox = wx.CheckBox(dlg, label="设为默认行为")
        sizer.Add(checkbox, 0, wx.ALL | wx.CENTER, 5)

        # 按钮区域
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        exit_btn = wx.Button(dlg, wx.ID_YES, "退出程序")
        minimize_btn = wx.Button(dlg, wx.ID_NO, "最小化到托盘")
        cancel_btn = wx.Button(dlg, wx.ID_CANCEL, "取消")

        btn_sizer.Add(exit_btn, 1, wx.ALL, 5)
        btn_sizer.Add(minimize_btn, 1, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 1, wx.ALL, 5)

        sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 5)
        dlg.SetSizer(sizer)

        # 绑定按钮事件
        def on_exit(evt):
            if checkbox.IsChecked():
                self.controller.config_manager.set_close_action("exit")
            self._do_exit()
            dlg.EndModal(wx.ID_YES)

        def on_minimize(evt):
            if checkbox.IsChecked():
                self.controller.config_manager.set_close_action("minimize")
            dlg.EndModal(wx.ID_NO)

        exit_btn.Bind(wx.EVT_BUTTON, on_exit)
        minimize_btn.Bind(wx.EVT_BUTTON, on_minimize)
        cancel_btn.Bind(wx.EVT_BUTTON, lambda evt: dlg.EndModal(wx.ID_CANCEL))

        # 显示对话框
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            # 退出程序
            event.Skip()
        elif result == wx.ID_NO:
            # 最小化到托盘
            self.Hide()
            event.Veto()
        else:  # wx.ID_CANCEL
            event.Veto()

    def _do_exit(self):
        """执行退出操作"""
        try:
            if self.controller.is_connected:
                asyncio.run_coroutine_threadsafe(self.controller.disconnect(), self.loop)
            self.taskbar_icon.Destroy()
            self.Destroy()
        except Exception as e:
            print(f"关闭程序错误：{e}")


def main():
    try:
        app = wx.App()
        frame = ChatFrame()
        frame.Show()

        # 启动事件循环
        def run_loop(loop):
            try:
                asyncio.set_event_loop(loop)
                loop.run_forever()
            except Exception as e:
                print(f"事件循环错误：{e}")

        loop_thread = threading.Thread(target=run_loop, args=(frame.loop,), daemon=True)
        loop_thread.start()

        app.MainLoop()
    except Exception as e:
        print(f"程序启动错误：{e}")
        raise


if __name__ == "__main__":
    main()
