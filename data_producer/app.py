import psycopg2
from psycopg2.extras import RealDictCursor
from os import environ
from kafka import KafkaProducer
import argparse
import logging
import os
import time
from json import dumps 



# takes the csvs and inserts them into the db, creating tables as needed
def setup_db(args):
    conn = psycopg2.connect(host=args.dbhost,
                            port=5432,
                            dbname=args.dbname,
                            user=args.dbusername,
                            password=args.dbpassword)

    cur = conn.cursor()

    # does images table exist
    tb_exists = "select exists(" \
                "select relname from pg_class where relname='"\
                + "images" + "')"
    cur.execute(tb_exists)
    if cur.fetchone()[0] is False:
        # make table
        cur.execute(
            'create table images('
            'URL VARCHAR, '
	    'FILENAME VARCHAR, '
            'LABEL VARCHAR, '
            'TYPE VARCHAR, '
            'STATUS VARCHAR);')
        conn.commit()
    elif args.cleartables == 1:
        logging.info('Clearing images table')
        cur.execute('delete from images;')
        conn.commit()

    # does models table exist
    tb_exists = "select exists(" \
                "select relname from pg_class where relname='"\
                + "models" + "')"
    cur.execute(tb_exists)
    if cur.fetchone()[0] is False:
        cur.execute(
            'create table models('
            'ID SERIAL PRIMARY KEY, '
            'URL VARCHAR, '
            'FILENAME VARCHAR, '
            'MODELNAME VARCHAR);')
        conn.commit()
    elif args.cleartables == 1:
        logging.info('Clearing models table')
        cur.execute('delete from models;')
        conn.commit()
 
    # copy image csv to db
    f = open(r'benign_images.csv', 'r')
    cur.copy_from(f, "images", sep=',')
    # copy model csv to db
    g = open(r'models.csv', 'r')
    cur.copy_from(g, "models", sep=',')
    conn.commit()
    f.close()

def main(args):
    logging.info('brokers={}'.format(args.brokers))
    logging.info('topic={}'.format(args.topic))
    logging.info('creating kafka producer')    
    producer = KafkaProducer(bootstrap_servers=args.brokers,
                             value_serializer=lambda x: 
                             dumps(x).encode('utf-8'))
    logging.info('finished creating kafka producer')

    while True:
        conn = psycopg2.connect(
                host = args.dbhost,
                port = 5432,
                dbname = args.dbname,
                user = args.dbusername,
                password = args.dbpassword)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = 'select URL, FILENAME, LABEL from images where status=%s'
            cur.execute(query,('Unprocessed',))
            res = cur.fetchall()
        except Exception:
            res = []
        cur.close()
        conn.close()
        for result in res:
            logging.info('JSON result: {}'.format(dumps(result)))
            producer.send(args.topic, value=result)
            time.sleep(3.0) # Artifical delay for testing
        time.sleep(130.0) # Artifical delay for testing

def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, "") != "" else default

def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    args.dbhost = get_arg('DBHOST', args.dbhost)
    args.dbname = get_arg('DBNAME', args.dbname)
    args.dbusername = get_arg('DBUSERNAME', args.dbusername)
    args.dbpassword = get_arg('DBPASSWORD', args.dbpassword)
    args.cleartables = get_arg('CLEARTABLES', args.cleartables)
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting kafka-python producer')
    parser = argparse.ArgumentParser(description='generate tables, fill database, then produce data from DB onto kafka topic')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='kafka:9092')
    parser.add_argument(
            '--topic',
            help='Topic to write to, env variable KAFKA_TOPIC',
            default='benign-images')
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
            '--cleartables',
            help='clear out tables before starting, env variable CLEARTABLES',
            default=1)
    cmdline_args = parse_args(parser)
    setup_db(cmdline_args)
    main(cmdline_args)
    logging.info('exiting')


