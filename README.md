# Adversarial Machine Learning Pipeline on OpenShift

### Overview
This project contains a demo of conducting adversarial machine learning example generation and model retraining using microservices on OpenShift. 

### Prerequisites

Persistent storage where adversarial images will be placed. For purposes of this demo a Dropbox API token associated to a single application folder is used. The `adversarial\_example\_generator` service can be modified to handle the storage of your choosing. You'll also need access to a running OpenShift cluster. 

### Running the demo

1. Start Postgresql service
```
oc new-app --name postgresql \
  -e POSTGRESQL_USER=redhat \
  -e POSTGRESQL_PASSWORD=redhat \
  -e POSTGRESQL_DATABASE=adversarial \
  centos/postgresql-95-centos7
```

2. Start Kafka service
```
oc create -f https://raw.githubusercontent.com/EldritchJS/adversarial_pipeline/master/openshift_templates/strimzi-0.1.0.yaml
oc new-app strimzi
```

3. Start adversarial example generator service
```
oc new-app eldritchjs/py36centos7~https://github.com/eldritchjs/adversarial_pipeline \
--context-dir=adversarial_example_generator \
-e KAFKA_BROKERS=kafka:9092 \
-e KAFKA_READ_TOPIC=benign-images \
-e KAFKA_WRITE_TOPIC=benign-batch-status \
-e BATCH_SIZE=13
-e MODEL_URL= \
-e MODEL_MIN=0 \
-e MODEL_MAX=255 \
-e ATTACK_TYPE=PGD \
-e DROPBOX_TOKEN=
```

4. Start adversarial training service

5. Start adversarial data producer service

```
oc new-app centos/python-36-centos7~https://github.com/eldritchjs/adversarial_pipeline \
  --context-dir=adversarial_data_producer \
  -e KAFKA_BROKERS=kafka:9092 \
  -e KAFKA_TOPIC=benign-images \
  -e DBHOST=postgresql \
  -e DBNAME=adversarial \
  -e DBUSERNAME=<YOUR DB USERNAME> \
  -e DBPASSWORD=<YOUR DB PASSWORD> \
  --name data-producer
```

6. Check logs to see progress. Once a batch threshold is reached for the number of images received, any adversarial images generated will be placed in your persistent storage. At that point retraining will be initiated.
  
