import pika

# connect to a broker on the local machine
# If we wanted to connect to a broker on a different machine we'd simply specify its name or IP address here
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# After Connection, we need to make sure the recipient queue exists
channel.queue_declare(queue='hello')


channel.basic_publish(
	exchange='',
	routing_key='hello',
	body='Hello World!'
)
print(" [x] Sent 'Hello World!'")


# Close the connection
connection.close()

# the broker was started without enough free disk space (by default it needs at least 200 MB free)
