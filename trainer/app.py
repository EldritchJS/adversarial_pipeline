import argparse
import logging
import os
import time
import urllib.request as urllib
from art.config import ART_DATA_PATH
from art.attacks.evasion import FastGradientMethod
from art.attacks.evasion import ProjectedGradientDescent
from art.utils import get_file
from art.classifiers import KerasClassifier
from keras.models import load_model
from keras.datasets import cifar10
from keras.utils.np_utils import to_categorical
from json import loads
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from kafka import KafkaConsumer
import dropbox
import psycopg2
from art.defences import AdversarialTrainer

def main(args):
    logging.info('brokers={}'.format(args.brokers))
    logging.info('readtopic={}'.format(args.readtopic))
    logging.info('creating kafka consumer')

    consumer = KafkaConsumer(
        args.readtopic,
        bootstrap_servers=args.brokers,
        value_deserializer=lambda val: loads(val.decode('utf-8')))
    logging.info("finished creating kafka consumer")

    if args.dbxtoken != '':
        dbx = dropbox.Dropbox(args.dbxtoken)
    else:
        dbx = None
        logging.info('No Dropbox token provided')

    while True:
        for message in consumer:
            if (message.value['status']=='Ready') and (message.value['modelurl']):
                logging.info('Received {}'.format(message.value))
                (X_train, y_train), (X_test, y_test) = cifar10.load_data()
                X_train = X_train.reshape(X_train.shape[0], 32, 32, 3).astype('float32')
                X_test = X_test.reshape(X_test.shape[0], 32, 32, 3).astype('float32')
                y_train = to_categorical(y_train, 10)
                y_test = to_categorical(y_test, 10)
                modelurl = message.value['modelurl']
                logging.info('model={}'.format(modelurl))
                model_filename = 'base_model.h5'
                location = os.path.join(ART_DATA_PATH, model_filename)
                try:
                    os.remove(location)
                except OSError as error:
                    pass
                path = get_file(model_filename, extract=False, path=ART_DATA_PATH, url=modelurl)
                kmodel = load_model(path) 
                model = KerasClassifier(kmodel, use_logits=False, clip_values=[args.min,args.max]) 
                logging.info('finished acquiring model')            
                imagefiles=dbx.files_list_folder('/images')
                adversaries=False 
                for dbximage in imagefiles.entries:
                    filepath = '/images/' + dbximage.name
                    filename = dbximage.name
                    label = filename.split('_')[-3]
                    response = dbx.files_download(filepath)[1]
                    img = Image.open(BytesIO(response.content))
                    logging.info('downloaded file {}'.format(dbximage.name))
                    image = np.array(img.getdata()).reshape(1,img.size[0], img.size[1], 3).astype('float32')
                    if adversaries is False:
                        X_adv = image
                        y_adv = [label]
                        adversaries = True
                    else:
                        X_adv = np.append(X_adv, image, axis=0)
                        y_adv = np.append(y_adv, [label], axis=0)
                y_adv = to_categorical(y_adv, 10)
                X_train = np.append(X_train, X_adv, axis=0)
                y_train = np.append(y_train, y_adv, axis=0) 
                if args.testmode==0:
                    model.fit(X_train, y_train, nb_epochs=83, batch_size=50) # Per ART 360 example
                else:
                    model.fit(X_train, y_train, nb_epochs=1, batch_size=50) # Testing only
                model.basename=model_filename.split('.')[0]
                adv_model_name = model_basename + '_adv'
                adv_model_filename = adv_model_name + '.h5'
                model.save(model_basename + '_adv.h5')
                # TODO Copy to model store

                conn = psycopg2.connect(
                    host = args.dbhost,
                    port = 5432,
                    dbname = args.dbname,
                    user = args.dbusername,
                    password = args.dbpassword)
                cur = conn.cursor()
                query = 'INSERT into models(URL, FILENAME, MODELNAME) VALUES(%s, %s, %s)'
                cur.execute(query, ('', adv_model_filename, adv_model_name)) 
                conn.commit()
                logging.info('updated database with new model')
                cur.close()
                conn.close()

def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, "") != "" else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.readtopic = get_arg('KAFKA_READ_TOPIC', args.readtopic)
    args.model = get_arg('MODEL_URL', args.model)
    args.min = get_arg('MODEL_MIN', args.min)
    args.max = get_arg('MODEL_MAX', args.max)
    args.dbxtoken = get_arg('DROPBOX_TOKEN', args.dbxtoken)
    args.dbhost = get_arg('DBHOST', args.dbhost)
    args.dbname = get_arg('DBNAME', args.dbname)
    args.dbusername = get_arg('DBUSERNAME', args.dbusername)
    args.dbtopic = get_arg('DBPASSWORD', args.dbpassword)   
    args.testmode = get_arg('TESTMODE', args.testmode)
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='consume some stuff on kafka')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='kafka:9092')
    parser.add_argument(
            '--readtopic',
            help='Topic to read from, env variable KAFKA_READ_TOPIC',
            default='benign-batch-status')
    parser.add_argument(
            '--model',
            help='URL of base model to retrain, env variable MODEL_URL',
            default='https://www.dropbox.com/s/96yv0r2gqzockmw/cifar-10_ratio%3D0.5.h5?dl=1')
    parser.add_argument(
            '--min',
            help='Normalization range min, env variable MODEL_MIN',
            default=0.0)   
    parser.add_argument(
            '--max',
            help='Normalization range min, env variable MODEL_MAX',
            default=255.0)        
    parser.add_argument(
            '--dbxtoken',
            help='API token for Dropbox, env variable DROPBOX_TOKEN')
    parser.add_argument(
            '--dbhost',
            help='hostname for postgresql database, env variable DBHOST',
            default='postgresql')
    parser.add_argument(
            '--dbname',
            help='database name to setup and watch, env variable DBNAME',
            default='adversarial')

    parser.add_argument(
            '--dbusername',
            help='username for the database, env variable DBUSERNAME',
            default='redhat')
    
    parser.add_argument(
            '--dbpassword',
            help='password for the database, env variable DBPASSWORD',
            default='redhat')

    parser.add_argument(
            '--testmode',
            help='reduced training time for faster testing purposes',
            default=0)

    args = parse_args(parser)
    main(args)
    logging.info('exiting')

