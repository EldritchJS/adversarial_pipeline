# Containerized model retraining service

Intended for deployment on an OpenShift cluster. Expects an available Kafka broker, it will listen on the `benign-batch-status` topic. 

The trainer expects messages on the topic to provide a JSON object with keys `Status` and `modelurl`. The trainer downloads the model and imports it, then downloads all adversarial example images on the persistent store. These images are added to the training data used to generate the base model, and then the model is trained. Upon completion, the trainer saves the model and places an entry for the updated model information in a Postgresql database.

The trainer service is created as follows:

```
oc new-app eldritchjs/centospy36tf:tf~https://github.com/eldritchjs/adversarial_pipeline \
--context-dir=trainer \
-e KAFKA_BROKERS=kafka:9092 \
-e KAFKA_READ_TOPIC=benign-batch-status \
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
