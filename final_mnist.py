from flask import Flask, jsonify, abort, make_response, request
from PIL import Image, ImageFilter
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import tensorflow as tf
import matplotlib.pyplot as plt
import cv2
import logging
import time

log = logging.getLogger()
log.setLevel('INFO')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

app = Flask(__name__)
KEYSPACE = "mnist_data"


def imageprepare():
    """
    This function returns the pixel values.
    The input is a png file location.
    """
    file_name = '/app/Big_Data/new.png'  # the location of the posted png
    # in terminal 'mogrify -format png *.jpg' convert jpg to png
    im = Image.open(file_name).convert('L')

    im.save("/app/Big_Data/sample.png")
    # plt.imshow(im)
    # plt.show()
    tv = list(im.getdata())  # get pixel values

    # normalize pixels to 0 and 1. 0 is pure white, 1 is pure black.
    tva = [(255 - x) * 1.0 / 255.0 for x in tv]
    # print(tva)
    return tva


def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)


def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)


def conv2d(x, W):
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')


def max_pool_2x2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')


def Prediction():
    """
    This function returns the predicted integer.
    The imput is the pixel values from the imageprepare() function.
    """
    result = imageprepare()
    x = tf.placeholder(tf.float32, [None, 784])
    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))

    W_conv1 = weight_variable([5, 5, 1, 32])
    b_conv1 = bias_variable([32])

    x_image = tf.reshape(x, [-1, 28, 28, 1])
    h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)
    h_pool1 = max_pool_2x2(h_conv1)

    W_conv2 = weight_variable([5, 5, 32, 64])
    b_conv2 = bias_variable([64])

    h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
    h_pool2 = max_pool_2x2(h_conv2)

    W_fc1 = weight_variable([7 * 7 * 64, 1024])
    b_fc1 = bias_variable([1024])

    h_pool2_flat = tf.reshape(h_pool2, [-1, 7 * 7 * 64])
    h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

    keep_prob = tf.placeholder(tf.float32)
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

    W_fc2 = weight_variable([1024, 10])
    b_fc2 = bias_variable([10])

    y_conv = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)

    init_op = tf.initialize_all_variables()

    """
    Load the model1.ckpt file.
    This file is loaded from outside the container.
    Use the model to predict the integer. Integer is returend as string.
    
    Based on the documentatoin at
    https://www.tensorflow.org/versions/master/how_tos/variables/index.html
    """
    saver = tf.train.Saver()
    with tf.Session() as sess:
        sess.run(init_op)
        saver.restore(sess, "/app/Big_Data/models/model1.ckpt")  # The location of the model previously stored
        # print ("Model restored.")

        prediction = tf.argmax(y_conv, 1)
        predint = prediction.eval(feed_dict={x: [result], keep_prob: 1.0}, session=sess)
        print(h_conv2)

        # print('recognize result:')
        # print(predint[0])
        return str(predint[0])


def insert_data(filename, result, cur_time):
    cluster = Cluster(contact_points=['127.0.0.1'], port=9042)
    session = cluster.connect()
    
    try:
        session.execute("""
        CREATE KEYSPACE %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
        """ % KEYSPACE)
        log.info("Setting keyspace")
        session.set_keyspace(KEYSPACE)
        session.execute("""
           CREATE TABLE mytable (
           filename text,
           result text,
           time text,
           PRIMARY KEY (filename, time)
           )
           """)
    except Exception as error:
        log.error("Unable to create table")
        log.error(error)

    log.info("Setting keyspace")
    session.set_keyspace(KEYSPACE)

    log.info("Starting keyspace...")
    try:
        log.info("inserting table...")
        session.execute("""
           INSERT INTO mytable (filename, result, time)
           VALUES ('%s', '%s', '%s')
           """ % (filename, result, cur_time))
    except Exception as e:
        log.error("Unable to insert data")
        log.error(e)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save('/app/Big_Data/new.png')
        upload_filename = f.filename
        result = Prediction()
        cur_time = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        insert_data(upload_filename, result, cur_time)
    return "%s%s%s%s%s%s%s%s%s" % ("Upload File Name: ", upload_filename, "\n",
                                   "Result: ", result, "\n",
                                   "Upload Time: ", cur_time, "\n")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
