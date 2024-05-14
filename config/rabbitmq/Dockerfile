FROM rabbitmq:management

COPY rabbitmq_message_deduplication-0.6.2.ez /opt/rabbitmq/plugins/
COPY elixir-1.14.0.ez /opt/rabbitmq/plugins/

RUN rabbitmq-plugins enable rabbitmq_message_deduplication
