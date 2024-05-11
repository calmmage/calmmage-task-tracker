from bot_lib import App, Handler, HandlerDisplayMode


class MyApp(App):
    pass


class MyHandler(Handler):
    name = "main"
    display_mode = HandlerDisplayMode.FULL
    pass
