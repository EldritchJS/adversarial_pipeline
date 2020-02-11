# Image URL, filename, and label producer

This application sets up tables in a postgresql database, then begins sending JSON messages of the form `{"url":"<URL>","filename":"<FILENAME>","label":<LABEL>}` to a Kafka topic to which an adversarial example generator microservice is listening. It also listens to a batch topic which upon receiving a message prompts a message to be sent to an adversarial training microservice.


```oc new-app centos/python-36-centos7~https://github.com/eldritchjs/adversarial_pipeline \
  --context-dir=adversarial_data_producer \
  -e DBHOST=postgresql \
  -e DBNAME=adversarial \
  -e DBUSERNAME=username \
  -e DBPASSWORD=password```
