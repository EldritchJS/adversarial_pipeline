## Containerized adversarial example image generation

Intended for deployment on an OpenShift cluster. Expects an available Kafka broker, which can be created with the following commands:

1. `oc create -f https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/0.1.0/kafka-inmemory/resources/openshift-template.yaml`
2. `oc new-app strimzi`

The generator expects a JSON object with keys `url` and `label` for the url of the image to be attacked and its true label, respectively. It will attempt to generate an adversary image and report the model's prediction for the original image and its adversary.

`oc new-app centos/python-36-centos7~https://github.com/eldritchjs/url_label_producer`


The adversarial example image generator pod is created as follows:

`oc new-app centos/python-36-centos7~https://github.com/eldritchjs/adversarial_pipeline/adversarial_example_generator`
