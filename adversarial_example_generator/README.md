## Containerized adversarial example image generation

Intended for deployment on an OpenShift cluster. Expects an available Kafka broker, it will listen on the `images` topic.

The generator expects messages on the `images` topic to provide a JSON object with keys `url`, `filename`, and `label` for the url of the image to be attacked and its true label, respectively. It will attempt to generate an adversary image and report the model's prediction for the original image and its adversary.

The adversarial example image generator pod is created as follows:

```
oc new-app centos/python-36-centos7~https://github.com/eldritchjs/adversarial_pipeline \
--context-dir=adversarial_example_generator \
-e KAFKA_BROKERS=kafka:9092 \
-e KAFKA_READ_TOPIC=benign-images \
-e KAFKA_WRITE_TOPIC=benign-batch-status \
-e BATCH_SIZE=13'
-e MODEL_URL= \
-e MODEL_MIN='0' \
-e MODEL_MAX='255' \
-e ATTACK_TYPE='PGD' \
-e DROPBOX_TOKEN=
--name example-generator
```
