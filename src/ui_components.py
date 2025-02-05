from abc import ABC, abstractmethod
import wx
import wx.adv
import wx.html2
import markdown
from typing import List, Dict, Optional, Callable


class ServerPanel(wx.Panel):
    """服务器连接面板"""

    def __init__(self, parent, on_connect: Callable, on_favorite: Callable):
        super().__init__(parent)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.on_connect = on_connect
        self.on_favorite = on_favorite
        self.favorite_servers: List[str] = []

        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 服务器地址输入和选择
        ip_label = wx.StaticText(self, label="服务器地址:")
        self.ip_input = wx.ComboBox(self, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER, choices=[])
        self.ip_input.SetMinSize((250, -1))

        # 绑定输入事件
        self.ip_input.Bind(wx.EVT_TEXT, self._on_address_change)
        self.ip_input.Bind(wx.EVT_COMBOBOX, self._on_address_change)

        # 收藏按钮
        self.favorite_btn = wx.Button(self, label="☆", size=(30, -1))
        self.favorite_btn.SetToolTip("收藏当前地址")
        self.favorite_btn.Bind(wx.EVT_BUTTON, self._on_favorite_click)

        # 连接按钮
        self.connect_btn = wx.Button(self, label="连接")
        self.connect_btn.Bind(wx.EVT_BUTTON, self._on_connect_click)

        # 模型选择
        self.model_choice = wx.Choice(self, choices=[])
        self.model_choice.Disable()

        # 布局
        sizer.Add(ip_label, 0, wx.ALL | wx.CENTER, 5)
        sizer.Add(self.ip_input, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.favorite_btn, 0, wx.ALL | wx.CENTER, 5)
        sizer.Add(self.connect_btn, 0, wx.ALL | wx.CENTER, 5)
        sizer.Add(self.model_choice, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sizer)

    def _on_connect_click(self, event):
        self.on_connect(self.ip_input.GetValue())

    def _on_favorite_click(self, event):
        self.on_favorite(self.ip_input.GetValue())
        event.Skip()

    def _on_address_change(self, event):
        """处理地址变化事件"""
        current_address = self.ip_input.GetValue()
        is_favorite = current_address in self.favorite_servers
        self._do_update_favorite_button(is_favorite)
        event.Skip()

    def update_favorites(self, favorites: List[str]):
        """更新收藏列表"""
        self.favorite_servers = favorites
        current_url = self.ip_input.GetValue()
        self.ip_input.Clear()
        if favorites:
            self.ip_input.AppendItems(favorites)
        self.ip_input.SetValue(current_url)
        self._do_update_favorite_button(current_url in favorites)

    def _do_update_favorite_button(self, is_favorite: bool):
        """实际执行更新收藏按钮的操作"""
        self.favorite_btn.SetLabel("★" if is_favorite else "☆")
        self.favorite_btn.SetToolTip("取消收藏" if is_favorite else "收藏当前地址")
        self.favorite_btn.Refresh()

    def set_connecting_state(self):
        """设置连接中状态"""
        self.connect_btn.SetLabel("连接中...")
        self.connect_btn.Disable()
        self.ip_input.Disable()
        self.model_choice.Disable()
        self.favorite_btn.Disable()

    def set_connection_state(self, is_connected: bool):
        """设置连接状态"""
        self.connect_btn.SetLabel("断开" if is_connected else "连接")
        self.connect_btn.Enable()
        self.ip_input.Enable(not is_connected)
        self.model_choice.Enable(is_connected)
        self.favorite_btn.Enable()

    def update_models(self, models: List[Dict]):
        """更新模型列表"""
        self.model_choice.Clear()
        self.model_choice.AppendItems([model["name"] for model in models])
        if models:
            self.model_choice.SetSelection(0)

    def get_current_model(self) -> Optional[str]:
        """获取当前选中的模型"""
        index = self.model_choice.GetSelection()
        return self.model_choice.GetString(index) if index != wx.NOT_FOUND else None


class ChatPanel(wx.Panel):
    """聊天面板"""

    def __init__(self, parent, on_send: Callable):
        super().__init__(parent)
        self.on_send = on_send
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 聊天显示区域
        self.web_view = wx.html2.WebView.New(self)
        self.web_view.SetBackgroundColour(wx.Colour(255, 255, 255))

        # 输入区域
        input_panel = wx.Panel(self)
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.message_input = wx.TextCtrl(input_panel, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER, size=(-1, 60))
        self.message_input.SetMaxSize((-1, 60))
        self.message_input.Bind(wx.EVT_TEXT_ENTER, self._on_send)

        self.send_btn = wx.Button(input_panel, label="发送")
        self.send_btn.Bind(wx.EVT_BUTTON, self._on_send)
        self.send_btn.Disable()

        input_sizer.Add(self.message_input, 1, wx.ALL | wx.EXPAND, 5)
        input_sizer.Add(self.send_btn, 0, wx.ALL | wx.CENTER, 5)
        input_panel.SetSizer(input_sizer)

        sizer.Add(self.web_view, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(input_panel, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sizer)

    def _on_send(self, event):
        message = self.message_input.GetValue().strip()
        if message:
            self.on_send(message)

    def set_send_state(self, enabled: bool, is_sending: bool = False):
        """设置发送状态"""
        self.send_btn.Enable(enabled)
        self.send_btn.SetLabel("发送中..." if is_sending else "发送")
        self.message_input.Enable(enabled)
        if enabled and not is_sending:
            self.message_input.SetFocus()

    def clear_input(self):
        """清空输入框"""
        self.message_input.SetValue("")

    def update_chat_display(self, messages: List[Dict[str, str]]):
        """更新聊天显示"""
        html_content = self._generate_chat_html(messages)
        self.web_view.SetPage(html_content, "")

    def _generate_chat_html(self, messages: List[Dict[str, str]]) -> str:
        """生成聊天HTML内容"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    font-size: 14px;
                    line-height: 1.5;
                }
                .message {
                    margin-bottom: 20px;
                    padding: 15px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .user-message {
                    background-color: #e3f2fd;
                    margin-left: 20%;
                }
                .ai-message {
                    background-color: #ffffff;
                    margin-right: 20%;
                }
                .message-header {
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #666;
                    font-size: 12px;
                }
                pre {
                    position: relative;
                    background-color: #1e1e1e !important;
                    color: #d4d4d4;
                    padding: 1em 1.5em;
                    border-radius: 8px;
                    overflow-x: auto;
                    font-family: "SF Mono", "Cascadia Code", Menlo, Consolas, "DejaVu Sans Mono", monospace;
                    font-size: 13px;
                    line-height: 1.6;
                    margin: 1em 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                    border: 1px solid #333;
                }
                pre::before {
                    content: attr(data-language);
                    position: absolute;
                    top: 0;
                    right: 0;
                    padding: 4px 8px;
                    font-size: 12px;
                    font-weight: 600;
                    color: #d4d4d4;
                    background: #333;
                    border-radius: 0 8px 0 8px;
                }
                code {
                    font-family: "SF Mono", "Cascadia Code", Menlo, Consolas, "DejaVu Sans Mono", monospace;
                    background-color: #f3f4f6;
                    padding: 0.2em 0.4em;
                    border-radius: 4px;
                    font-size: 85%;
                    color: #24292e;
                }
                pre code {
                    background-color: transparent;
                    padding: 0;
                    font-size: inherit;
                    color: inherit;
                    white-space: pre;
                    word-break: normal;
                    word-wrap: normal;
                }
                /* VS Code Dark+ 主题配色 */
                .codehilite .hll { background-color: #3c3c3c }
                .codehilite .c { color: #6a9955 } /* Comment */
                .codehilite .err { color: #f44747 } /* Error */
                .codehilite .k { color: #569cd6 } /* Keyword */
                .codehilite .l { color: #ce9178 } /* Literal */
                .codehilite .n { color: #d4d4d4 } /* Name */
                .codehilite .o { color: #d4d4d4 } /* Operator */
                .codehilite .p { color: #d4d4d4 } /* Punctuation */
                .codehilite .cm { color: #6a9955 } /* Comment.Multiline */
                .codehilite .cp { color: #6a9955 } /* Comment.Preproc */
                .codehilite .c1 { color: #6a9955 } /* Comment.Single */
                .codehilite .cs { color: #6a9955 } /* Comment.Special */
                .codehilite .kc { color: #569cd6 } /* Keyword.Constant */
                .codehilite .kd { color: #569cd6 } /* Keyword.Declaration */
                .codehilite .kn { color: #569cd6 } /* Keyword.Namespace */
                .codehilite .kp { color: #569cd6 } /* Keyword.Pseudo */
                .codehilite .kr { color: #569cd6 } /* Keyword.Reserved */
                .codehilite .kt { color: #569cd6 } /* Keyword.Type */
                .codehilite .ld { color: #ce9178 } /* Literal.Date */
                .codehilite .m { color: #b5cea8 } /* Literal.Number */
                .codehilite .s { color: #ce9178 } /* Literal.String */
                .codehilite .na { color: #9cdcfe } /* Name.Attribute */
                .codehilite .nb { color: #dcdcaa } /* Name.Builtin */
                .codehilite .nc { color: #4ec9b0 } /* Name.Class */
                .codehilite .no { color: #4fc1ff } /* Name.Constant */
                .codehilite .nd { color: #dcdcaa } /* Name.Decorator */
                .codehilite .ni { color: #d4d4d4 } /* Name.Entity */
                .codehilite .ne { color: #f44747 } /* Name.Exception */
                .codehilite .nf { color: #dcdcaa } /* Name.Function */
                .codehilite .nl { color: #d4d4d4 } /* Name.Label */
                .codehilite .nn { color: #d4d4d4 } /* Name.Namespace */
                .codehilite .nx { color: #4ec9b0 } /* Name.Other */
                .codehilite .py { color: #d4d4d4 } /* Name.Property */
                .codehilite .nt { color: #569cd6 } /* Name.Tag */
                .codehilite .nv { color: #9cdcfe } /* Name.Variable */
                .codehilite .ow { color: #569cd6 } /* Operator.Word */
                .codehilite .mb { color: #b5cea8 } /* Literal.Number.Bin */
                .codehilite .mf { color: #b5cea8 } /* Literal.Number.Float */
                .codehilite .mh { color: #b5cea8 } /* Literal.Number.Hex */
                .codehilite .mi { color: #b5cea8 } /* Literal.Number.Integer */
                .codehilite .mo { color: #b5cea8 } /* Literal.Number.Oct */
                .codehilite .sa { color: #ce9178 } /* Literal.String.Affix */
                .codehilite .sb { color: #ce9178 } /* Literal.String.Backtick */
                .codehilite .sc { color: #ce9178 } /* Literal.String.Char */
                .codehilite .dl { color: #ce9178 } /* Literal.String.Delimiter */
                .codehilite .sd { color: #6a9955 } /* Literal.String.Doc */
                .codehilite .s2 { color: #ce9178 } /* Literal.String.Double */
                .codehilite .se { color: #ce9178 } /* Literal.String.Escape */
                .codehilite .sh { color: #ce9178 } /* Literal.String.Heredoc */
                .codehilite .si { color: #ce9178 } /* Literal.String.Interpol */
                .codehilite .sx { color: #ce9178 } /* Literal.String.Other */
                .codehilite .sr { color: #d16969 } /* Literal.String.Regex */
                .codehilite .s1 { color: #ce9178 } /* Literal.String.Single */
                .codehilite .ss { color: #ce9178 } /* Literal.String.Symbol */
            </style>
            <script>
                function scrollToBottom() {
                    window.scrollTo(0, document.body.scrollHeight);
                }
                
                // 为代码块添加语言标识
                document.addEventListener('DOMContentLoaded', function() {
                    document.querySelectorAll('pre').forEach(function(pre) {
                        var code = pre.querySelector('code');
                        if (code && code.className) {
                            var lang = code.className.split('-')[1];
                            if (lang) {
                                pre.setAttribute('data-language', lang);
                            }
                        }
                    });
                });
            </script>
        </head>
        <body onload="scrollToBottom()">
        """

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                html_content = f"""
                <div class="message user-message">
                    <div class="message-header">用户</div>
                    <div>{content}</div>
                </div>
                """
            else:
                md = markdown.markdown(
                    content,
                    extensions=["fenced_code", "codehilite", "tables"],
                    extension_configs={
                        "codehilite": {
                            "css_class": "codehilite",
                            "use_pygments": True,
                            "noclasses": False,
                            "guess_lang": True,
                        }
                    },
                )
                html_content = f"""
                <div class="message ai-message">
                    <div class="message-header">AI</div>
                    <div>{md}</div>
                </div>
                """
            html_template += html_content

        html_template += """
        </body>
        </html>
        """

        return html_template


class TaskBarIcon(wx.adv.TaskBarIcon):
    """系统托盘图标"""

    def __init__(self, frame):
        super().__init__()
        self.frame = frame
        # self.SetIcon(self.frame.icon, "Ollama AI\n点击显示/隐藏窗口\n右键查看菜单")
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        """创建右键菜单"""
        menu = wx.Menu()

        show_item = menu.Append(wx.ID_ANY, "显示" if not self.frame.IsShown() else "隐藏")
        self.Bind(wx.EVT_MENU, self.on_show, show_item)

        menu.AppendSeparator()

        exit_item = menu.Append(wx.ID_ANY, "退出")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

        return menu

    def on_left_down(self, event):
        """处理左键点击事件"""
        if self.frame.IsShown():
            self.frame.Hide()
        else:
            self.frame.Show()
            self.frame.Restore()
            self.frame.Raise()

    def on_show(self, event):
        """处理显示/隐藏菜单项"""
        if self.frame.IsShown():
            self.frame.Hide()
        else:
            self.frame.Show()
            self.frame.Restore()
            self.frame.Raise()

    def on_exit(self, event):
        """处理退出菜单项"""
        self.frame._do_exit()
        self.frame.Close(True)
