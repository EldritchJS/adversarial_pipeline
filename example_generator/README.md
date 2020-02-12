# Containerized adversarial example image generation service

Intended for deployment on an OpenShift cluster. Expects an available Kafka broker, it will listen on the `benign-images` topic.

The generator expects messages on the `benign-images` topic to provide a JSON object with keys `url`, `filename`, and `label` for the url of the image to be attacked, its filename true label, respectively. It will attempt to generate an adversary image and report the model's prediction for the original image and its adversary in logs. Any adversarial examples created will then be copied to persistent storage, for this example Dropbox is used.

The adversarial example image generator pod is created as follows:

```
oc new-app eldritchjs/centospy36tf:tf~https://github.com/eldritchjs/adversarial_pipeline \
--context-dir=example_generator \
-e KAFKA_BROKERS=kafka:9092 \
-e KAFKA_READ_TOPIC=benign-images \
-e KAFKA_WRITE_TOPIC=benign-batch-status \
-e BATCH_SIZE=6'
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
