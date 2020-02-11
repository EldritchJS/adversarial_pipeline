import psycopg2
from os import environ
from kafka import KafkaProducer
import argparse
import logging
import os
import time
from json import dumps 



class DatabaseLoader:
    # main function
    def __init__(self):
        self.server = environ.get("DBHOST")
        self.user = environ.get("DBUSERNAME")
        self.password = environ.get("DBPASSWORD")
        self.dbname = environ.get("DBNAME")
        self.cleartables = environ.get("CLEARTABLES")

    # takes the csv and inserts it into the db
    def setup_db(self):
        conn = psycopg2.connect(host=self.server,
                                port=5432,
                                dbname=self.dbname,
                                user=self.user,
                                password=self.password)

        cur = conn.cursor()

        # does table exist
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
        elif self.cleartables == '1':
            cur.execute('delete from images;')
            conn.commit()

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
        elif self.cleartables == '1':
            cur.execute('delete from models;')
            conn.commit()
        # copy csv
        f = open(r'benign_images.csv', 'r')
        cur.copy_from(f, "images", sep=',')
        g = open(r'models.csv', 'r')
        cur.copy_from(g, "models", sep=',')
        conn.commit()
        f.close()

def main(args):
    logging.info('brokers={}'.format(args.brokers))
    logging.info('topic={}'.format(args.topic))
    logging.info('creating kafka producer')    
    producer = KafkaProducer(bootstrap_servers=['kafka:9092'],
                             value_serializer=lambda x: 
                             dumps(x).encode('utf-8'))
    logging.info('finished creating kafka producer')

    while True:
        con = psycopg2.connect(
                host = args.dbhost,
                port = 5432,
                dbname = args.dbname)
                user = args.dbusername,
                password = args.dbpassword,
        cur = con.cursor()
        try:
            query = 'select * from images where status=%s'
            cur.execute(query, ('"Unprocessed"',))
            res = [i[0] for i in cur.fetchall()]
        except Exception:
            res = []
        cur.close()
        con.close()
        for result in res:
            logging.info('Result: {}'.format
#            producer.send('images', value=json.jsonify(result))
            time.sleep(15.0)

def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default

def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    args.dbhost = get_arg('DBHOST', args.dbhost)
    args.dbtopic = get_arg('DBNAME', args.dbname)
    args.dbusername = get_arg('DBUSERNAME', args.dbusername)
    args.dbtopic = get_arg('DBPASSWORD', args.dbpassword)
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
            default='images')
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
            default='0')
    args = parse_args(parser)
    dbl = DatabaseLoader()
    dbl.setup_db()
    main(args)
    logging.info('exiting')


