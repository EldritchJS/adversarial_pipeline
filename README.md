# adversarial_pipeline

Prerequisites:

Persistent storage where adversarial images will be placed. For purposes of this demo a Dropbox API token associated to a single application folder is used. The `adversarial\_example\_generator` service can be modified to handle the storage of your choosing. 

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

4. Start adversarial training service

5. Start adversarial data producer service

```
oc new-app centos/python-36-centos7~https://github.com/eldritchjs/adversarial_pipeline \
  --context-dir=adversarial_data_producer \
  -e DBHOST=postgresql \
  -e DBNAME=adversarial \
  -e DBUSERNAME=username \
  -e DBPASSWORD=password
```

6. Check logs to see progress. Once a batch threshold is reached for the number of images received, any adversarial images generated will be placed in your persistent storage. At that point retraining will be initiated.
  
