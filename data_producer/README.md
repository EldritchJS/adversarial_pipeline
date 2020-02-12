# Image URL, filename, and label data producer

This application sets up tables in a postgresql database, then begins sending JSON messages of the form `{"url":"<URL>","filename":"<FILENAME>","label":<LABEL>,"type":[Benign|Adversarial],"status":[Unprocessed|Processed]}` to a Kafka topic to which an adversarial example generator microservice is listening. 

```
oc new-app centos/python-36-centos7~https://github.com/eldritchjs/adversarial_pipeline \
  --context-dir=data_producer \
  -e KAFKA_BROKERS=kafka:9092 \
  -e KAFKA_TOPIC=benign-images \
  -e DBHOST=postgresql \
  -e DBNAME=adversarial \
  -e DBUSERNAME=redhat \
  -e DBPASSWORD=redhat \
  -e CLEARTABLES=1 \
  --name data-producer
```
