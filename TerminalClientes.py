import os
import flask
import tornado.web
import tornado.wsgi
import tornado_xstatic

from abc import ABC
from tornado.ioloop import IOLoop
from terminado import TermSocket, UniqueTermManager

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(TEMPLATE_DIR, "static")


class TerminalPageHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        return self.render("termpage.html", static=self.static_url,
                           xstatic=self.application.settings['xstatic_url'],
                           ws_url_path="/websocket")


class Terminal:

    def __init__(self, app=None):
        self.app = app
        self.tornado_app = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        pass

    def add_terminal(self, route, command):
        assert route.startswith('/')
        if self.app is None:
            raise Exception("we don't support init_app yet")
        term_manager = UniqueTermManager(shell_command=command)
        wrapped_app = tornado.wsgi.WSGIContainer(self.app)
        handlers = [
            (r"/websocket", TermSocket, {'term_manager': term_manager}),
            (route, TerminalPageHandler),
            (r"/xstatic/(.*)", tornado_xstatic.XStaticFileHandler, {'allowed_modules': ['termjs']},),
            ("/(.*)", tornado.web.FallbackHandler, {'fallback': wrapped_app}),
        ]
        self.tornado_app = tornado.web.Application(handlers, static_path=STATIC_DIR,
                                                   template_path=TEMPLATE_DIR,
                                                   xstatic_url=tornado_xstatic.url_maker('/xstatic/'))

    def run(self, port=8000, host='127.0.0.1'):
        self.tornado_app.listen(port, host)
        IOLoop.current().start()


app = flask.Flask(__name__)


@app.route('/')
def home():
    return 'home'


if __name__ == '__main__':
    terminal = Terminal(app)
    terminal.add_terminal('/cmd', ['bash', '/home/jonathan/Desktop/script.sh'])
    terminal.run()

