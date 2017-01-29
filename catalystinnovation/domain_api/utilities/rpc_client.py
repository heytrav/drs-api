
import pika
import uuid
import json

class EppRpcClient(object):
    """
    This is based on the rpc client example in
    this tutorial:

    https://www.rabbitmq.com/tutorials/tutorial-six-python.html

    """
    def __init__(self,
                 host=None,
                 port=5672,
                 login='guest',
                 password='guest',
                 vhost="/"):
        credentials = pika.PlainCredentials(login, password)

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host, port, vhost, credentials)
        )

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, exchange, routing_key, data):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange=exchange,
                                   routing_key=routing_key,
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=data)
        while self.response is None:
            self.connection.process_data_events()
        return json.loads(self.response.decode("utf-8"))
