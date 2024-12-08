import pandas as pd
import numpy as np
import sklearn as sk
import category_encoders as ce
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from scipy.spatial.distance import cdist


'read data'
def preprocess_data():
    spotify_df = pd.read_csv('datasets/spotify-track-dataset.csv')
    features = spotify_df[['danceability', 'energy', 'loudness', 'acousticness', 'instrumentalness', 
                        'valence', 'tempo']]

    scaler = MinMaxScaler()
    features = scaler.fit_transform(features)

    sequence_length = 10
    X = []
    Y = []

    for i in range(len(features) - sequence_length):
        X.append(features[i:i + sequence_length])
        Y.append(features[i + sequence_length])

    X = np.array(X)
    Y = np.array(Y)

    return spotify_df, X, Y


'build lstm model'
def build_model(input_shape):
    model = Sequential()
    model.add(LSTM(128, input_shape=(sequence_length, X.shape[2]), return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(64))
    model.add(Dropout(0.2))
    model.add(Dense(X.shape[2], activation='linear'))
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model


'return track ids of reccommended songs'
def recommend_songs(model, features, spotify_df, sequence):
    predicted_features = model.predict(sequence)
    distances = cdist(features, predicted_features)
    song_indices = np.argsort(distances.flatten())

    recommended_track_ids = []
    seen_tracks = set()

    spotify_df = spotify_df.reset_index()

    for idx in song_indices:
        if len(recommended_track_ids) == 10:  
            break
        if idx >= len(spotify_df):
            continue
        track_name = spotify_df.iloc[idx]['track_name']    
        if track_name not in seen_tracks:
            recommended_track_ids.append(spotify_df.iloc[idx]['track_id'])
            seen_tracks.add(track_name) 

    return recommended_track_ids    


'main code'
spotify_df, X, Y = preprocess_data()
sequence_length = 10
features = X.reshape(-1, X.shape[2])

#split dataset
X_train, X_val, y_train, y_val = train_test_split(X, Y, test_size=0.2, random_state=42)

#train model
model = build_model((sequence_length, X.shape[2]))
model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_val, y_val))



