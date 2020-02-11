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
from json import loads
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from kafka import KafkaConsumer
from kafka import KafkaProducer
import dropbox
import psycopg2

def main(args):
    batch_status_message = {'status':'Ready','model_url':args.model}
    batch_count = 0
    model_filename = 'base_model.h5'

    logging.info('model={}'.format(args.model))
    location = os.path.join(ART_DATA_PATH, model_filename)
    try:
        os.remove(location)
    except OSError as error:
        pass
    path = get_file(model_filename, extract=False, path='/home/jschlessman', url=args.model)
    kmodel = load_model(path) 
    model = KerasClassifier(kmodel, use_logits=False, clip_values=[args.min,args.max]) 
    logging.info('finished acquiring model')
    logging.info('creating attack {}'.format(args.attack))

    if args.attack == 'FGM':
        attack = FastGradientMethod(model, eps=0.3, eps_step=0.01, targeted=False) 
    elif args.attack == 'PGD':
        attack = ProjectedGradientDescent(model, eps=8, eps_step=2, max_iter=13, targeted=False, num_random_init=True)
    else:
        logging.error('Invalid attack provided {} must be one of {FGM, PGD}'.format(args.attack))
        exit(0)

    logging.info('finished creating attack')
    logging.info('brokers={}'.format(args.brokers))
    logging.info('readtopic={}'.format(args.readtopic))
    logging.info('creating kafka consumer')

    consumer = KafkaConsumer(
        args.readtopic,
        bootstrap_servers=args.brokers,
        value_deserializer=lambda val: loads(val.decode('utf-8')))
    logging.info("finished creating kafka consumer")

    if args.dbxtoken != None:
        dbx = dropbox.Dropbox(args.dbxtoken)
        logging.info('creating kafka producer')    
        producer = KafkaProducer(bootstrap_servers=['kafka:9092'],
                                 value_serializer=lambda x: 
                                 dumps(x).encode('utf-8'))
        logging.info('finished creating kafka producer')    
    else:
        dbx = None

    while True:
        for message in consumer:
            if message.value['url']:
                conn = psycopg2.connect(
                    host = args.dbhost,
                    port = 5432,
                    dbname = args.dbname,
                    user = args.dbusername,
                    password = args.dbpassword)
                cur = conn.cursor()
                query = 'UPDATE images SET STATUS=%s where URL=%s'
                cur.execute(query, ('Processed', image_url))
                cur.close()
                conn.close()
                batch_count = batch_count+1
                image_url = message.value['url']
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content))
                label = message.value['label']
                infilename = message.value['filename'].rpartition('.')[0]
                logging.info('received URL {}'.format(image_url))
                logging.info('received label {}'.format(label))
                logging.info('received filename {}'.format(infilename))
                logging.info('downloading image')
                image = np.array(img.getdata()).reshape(1,img.size[0], img.size[1], 3).astype('float32')
                logging.info('downloaded image')
                images = np.ndarray(shape=(2,32,32,3))
                images[0] = image
                adversarial = attack.generate(image)
                images[1] = adversarial
                logging.info('adversarial image generated')
                preds = model.predict(images)
                orig_inf = np.argmax(preds[0])
                adv_inf = np.argmax(preds[1])
                logging.info('original inference: {}  adversarial inference: {}'.format(orig_inf, adv_inf))
                if (orig_inf != adv_inf) and (dbx != None):
                    fs=BytesIO()
                    imout=Image.fromarray(np.uint8(adversarial[0]))
                    im.save(fs, format='jpeg')
                    outfilename = '/images/{}_{}_adv.jpg'.format(infilename,adv_inf) 
                    dbx.files_upload(fs.getvalue(), outfilename)
                if (batch_count == args.batchsize) and (dbx != None):
                    producer.send(args.writetopic,batch_status_message)
                    batch_count=0



def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.readtopic = get_arg('KAFKA_READ_TOPIC', args.readtopic)
    args.writetopic = get_arg('KAFKA_WRITE_TOPIC', args.writetopic)
    args.model = get_arg('MODEL_URL', args.model)
    args.min = get_arg('MODEL_MIN', args.min)
    args.max = get_arg('MODEL_MAX', args.max)
    args.attack = get_arg('ATTACK_TYPE', args.attack)
    args.dbxtoken = get_arg('DROPBOX_TOKEN', args.dbxtoken)
    args.batchsize = get_arg('BATCH_SIZE', args.batchsize)
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting kafka-python consumer')
    parser = argparse.ArgumentParser(description='consume some stuff on kafka')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='kafka:9092')
    parser.add_argument(
            '--readtopic',
            help='Topic to read from, env variable KAFKA_WRITE_TOPIC',
            default='benign-images')
    parser.add_argument(
            '--writetopic',
            help='Topic to read from, env variable KAFKA_READ_TOPIC',
            default='benign-batch-status')    
    parser.add_argument(
            '--model',
            help='URL of base model to retrain, env variable MODEL_URL',
            default='https://www.dropbox.com/s/96yv0r2gqzockmw/cifar-10_ratio%3D0.5.h5?dl=1')
    parser.add_argument(
            '--min',
            help='Normalization range min, env variable MODEL_MIN',
            default=0)   
    parser.add_argument(
            '--max',
            help='Normalization range min, env variable MODEL_MAX',
            default=255)        
    parser.add_argument(
            '--attack',
            help='Attack for adversarial example generation [FGM | PGD], env variable ATTACK_TYPE',
            default='PGD')
    parser.add_argument(
            '--dbxtoken',
            help='API token for Dropbox, env variable DROPBOX_TOKEN',
            default=None)
    parser.add_argument(
            '--batchsize',
            help='Adversarial batch size, env variable BATCH_SIZE',
            default=3)
    args = parse_args(parser)
    main(args)
    logging.info('exiting')

