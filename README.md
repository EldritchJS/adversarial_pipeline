# Adversarial Machine Learning Pipeline on OpenShift

### Overview
This project contains a demo of conducting adversarial machine learning example generation and model retraining using microservices on OpenShift. 

### Prerequisites

Persistent storage where adversarial images will be placed. For purposes of this demo a Dropbox API token associated to a single application folder is used. The `example_generator` and `trainer` services can be modified to handle the storage of your choosing. You'll also need access to a running OpenShift cluster. 

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

3. Start example generator service

```
oc new-app eldritchjs/py36centostf:tf:tf~https://github.com/eldritchjs/adversarial_pipeline \
--context-dir=example_generator \
-e KAFKA_BROKERS=kafka:9092 \
-e KAFKA_READ_TOPIC=benign-images \
-e KAFKA_WRITE_TOPIC=benign-batch-status \
-e BATCH_SIZE=5 \
-e MODEL_URL=https://www.dropbox.com/s/96yv0r2gqzockmw/cifar-10_ratio%3D0.5.h5?dl=1 \
-e MODEL_MIN=0 \
-e MODEL_MAX=255 \
-e ATTACK_TYPE=PGD \
-e DROPBOX_TOKEN= \
-e DBHOST=postgresql \
-e DBNAME=adversarial \
-e DBUSERNAME=redhat \
-e DBPASSWORD=redhat \
--name example-generator
```

4. Start training service

```
oc new-app eldritchjs/py36centostf:tf~https://github.com/eldritchjs/adversarial_pipeline \
--context-dir=trainer \
-e KAFKA_BROKERS=kafka:9092 \
-e KAFKA_READ_TOPIC=benign-batch-status \
-e BATCH_SIZE=6 \
-e MODEL_URL=https://www.dropbox.com/s/96yv0r2gqzockmw/cifar-10_ratio%3D0.5.h5?dl=1 \
-e MODEL_MIN=0 \
-e MODEL_MAX=255 \
-e DROPBOX_TOKEN= \
-e DBHOST=postgresql \
-e DBNAME=adversarial \
-e DBUSERNAME=redhat \
-e DBPASSWORD=redhat \
--name trainer
```

5. Start data producer service

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

6. Check logs to see progress. Once a batch threshold is reached for the number of images received, any adversarial images generated will be placed in your persistent storage. At that point retraining will be initiated.
  
