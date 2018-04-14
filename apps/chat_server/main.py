#!/usr/bin/env python
import json
import uuid
import logging
import os.path

import tornado
import tornado.gen
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.concurrent
import tornado.options
import tornadoredis
import tornadoredis.pubsub


tornado.options.define("port", default=8888, help="run on the given port", type=int)
tornado.options.define("debug", default=False, help="run in debug mode")

# TODO need implements "service discovery" and "registrator" patterns for using redis settings
tornado.options.define("global_pubsub_channel",default="test-tornado-chat", help="redis global broadcast channel name", type=str)
tornado.options.define("redis_host", default="localhost", help="redis service host", type=str)
tornado.options.define("redis_port", default=6379, help="redis service host", type=int)

# all servers broadcast to global redis pubsub channel, and don't sync messages order in global_message_buffer on different messages
class GlobalServersSubscriber(tornadoredis.pubsub.BaseSubscriber):
    def on_message(self, msg):
        if msg.kind == 'message' and msg.body:
            subscribers = list(self.subscribers[msg.channel].keys())
            if subscribers:
                for s in subscribers:
                    s.new_messages([json.loads(msg.body)])

        super(GlobalServersSubscriber, self).on_message(msg)

global_servers_pubsub = GlobalServersSubscriber(None)


class MessageBuffer(object):
    def __init__(self):
        self.waiters = set()
        self.cache = []
        self.cache_size = 200

    def wait_for_messages(self, cursor=None):
        # Construct a Future to return to our caller.  This allows
        # wait_for_messages to be yielded from a coroutine even though
        # it is not a coroutine itself.  We will set the result of the
        # Future when results are available.
        result_future = tornado.concurrent.Future()
        if cursor:
            new_count = 0
            for msg in reversed(self.cache):
                if msg["id"] == cursor:
                    break
                new_count += 1
            if new_count:
                result_future.set_result(self.cache[-new_count:])
                return result_future
        self.waiters.add(result_future)
        return result_future

    def cancel_wait(self, future):
        self.waiters.remove(future)
        # Set an empty result to unblock any coroutines waiting.
        future.set_result([])

    def new_messages(self, messages):
        logging.info("Sending new message to %r listeners", len(self.waiters))
        for future in self.waiters:
            future.set_result(messages)
        self.waiters = set()
        clean_messages=[]
        for msg in messages:
            is_exists=False
            for cached_msg in self.cache:
                if cached_msg['id']==msg['id']:
                    is_exists=True
            if not is_exists:
                clean_messages.append(msg)
        self.cache.extend(clean_messages)
        if len(self.cache) > self.cache_size:
            self.cache = self.cache[-self.cache_size:]


# Making this a non-singleton is left as an exercise for the reader.
global_message_buffer = MessageBuffer()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", messages=global_message_buffer.cache)


class MessageNewHandler(tornado.web.RequestHandler):
    def post(self):
        message = {
            "id": str(uuid.uuid4()),
            "nick": self.get_argument("nick"),
            "body": self.get_argument("body"),
        }
        # to_basestring is necessary for Python 3's json encoder,
        # which doesn't accept byte strings.
        message["html"] = tornado.escape.to_basestring(
            self.render_string("message.html", message=message))
        if self.get_argument("next", None):
            self.redirect(self.get_argument("next"))
        else:
            self.write(message)
        global_message_buffer.new_messages([message])
        global_servers_pubsub.publish(
            tornado.options.options.global_pubsub_channel,
            message,
            tornadoredis.Client(
                tornado.options.options.redis_host,
                tornado.options.options.redis_port,
            )
        )


class MessageUpdatesHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        cursor = self.get_argument("cursor", None)
        # Save the future returned by wait_for_messages so we can cancel
        # it in wait_for_messages
        self.future = global_message_buffer.wait_for_messages(cursor=cursor)
        messages = yield self.future
        if self.request.connection.stream.closed():
            return
        self.write(dict(messages=messages))

    def on_connection_close(self):
        global_message_buffer.cancel_wait(self.future)


def main():
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/chat/message/new", MessageNewHandler),
            (r"/chat/message/updates", MessageUpdatesHandler),
        ],
        cookie_secret="__I_DONT_UNDERSTAND_HOWTO_TEST_THIS_APPLICATION__",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        debug=tornado.options.options.debug,
    )
    app.listen(tornado.options.options.port)
    logging.info("Application listen on %s" % tornado.options.options.port)

    global_servers_pubsub.redis = tornadoredis.Client(
        tornado.options.options.redis_host,
        tornado.options.options.redis_port,
    )
    global_servers_pubsub.subscribe(tornado.options.options.global_pubsub_channel, global_message_buffer)
    logging.info("Redis subscribed on %s" % tornado.options.options.global_pubsub_channel)
    logging.info("Starting IOLoop...")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
