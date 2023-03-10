# -*- coding: utf-8 -*-
"""TimeSeriesSubmission.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yIhqb5BI7jwM8t70rwY-smZax3-XxKXQ
"""

# Install Kaggle
! pip install kaggle

# Mount ke Google Drive
from google.colab import drive
drive.mount('/content/gdrive')

# Setup folder
import os
os.environ['KAGGLE_CONFIG_DIR'] = "/content/gdrive/My Drive/Kaggle"

# Download Dataset
!kaggle datasets download -d jaganadhg/house-hold-energy-data

# Unzip dataset
!unzip \*.zip && rm *.zipa

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

# get dataset
df = pd.read_csv("D202.csv")

# Remove unused columns
df = df.drop(columns=["NOTES", "START TIME", "END TIME", "UNITS", "COST", "TYPE"])

# Convert string to date time format
df['DATE'] = pd.to_datetime(df['DATE'])

df.tail(10)

# check types
df.dtypes

# check null
df.isnull().sum()

# Visualize data
figure(figsize=(12, 5), dpi=80, linewidth=10)
plt.plot(df['DATE'].values, df['USAGE'].values)
plt.title('Electric Usage')
plt.xlabel('Years', fontsize=14)
plt.ylabel('Usage', fontsize=14)
plt.show()

from sklearn.preprocessing import MinMaxScaler
mx = MinMaxScaler()

# Normalization
df['USAGE'] = mx.fit_transform(df[['USAGE']])

date = df['DATE'].values
usage = df['USAGE'].values

from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(usage, date, train_size=0.8, test_size=0.2, shuffle=False)

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

import tensorflow as tf

# Get threshold MAE
threshold_mae = (df['USAGE'].max() - df['USAGE'].min()) * 10/100

print(threshold_mae)

train_set = windowed_dataset(x_train, window_size=64, batch_size=1024, shuffle_buffer=1000)
val_set = windowed_dataset(x_test, window_size=64, batch_size=1024, shuffle_buffer=1000)
model = tf.keras.models.Sequential([
    tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(60, return_sequences=True)),
    tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(60)),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dense(1),
])

optimizer = tf.keras.optimizers.SGD(learning_rate=1.0000e-04, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae') < 0.1 and logs.get('val_mae')< 0.1 ):
      print("\nMAE dari model < 10% skala data")
      self.model.stop_training = True
callbacks = myCallback()

history = model.fit(train_set, validation_data = val_set, epochs=100, callbacks=[callbacks])