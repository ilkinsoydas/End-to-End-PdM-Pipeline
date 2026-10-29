import tensorflow as tf
from tensorflow.keras import Sequential, Model
from tensorflow.keras.layers import (
    Input, LSTM, Dense, Dropout,
    Bidirectional, Attention,
    GlobalAveragePooling1D
)

# 1. Vanilla LSTM
def build_vanilla_lstm():
    model = Sequential([
        Input(shape=(256, 18)),
        LSTM(64),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1)
    ])
    return model


# 2. Stacked LSTM
def build_stacked_lstm():
    model = Sequential([
        Input(shape=(256, 18)),
        LSTM(64, return_sequences=True),
        LSTM(32),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1)
    ])
    return model


# 3. Bidirectional LSTM
def build_bidirectional_lstm():
    model = Sequential([
        Input(shape=(256, 18)),
        Bidirectional(LSTM(64)),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1)
    ])
    return model


# 4. BiLSTM + Attention
def build_bilstm_attention():
    inputs = Input(shape=(256, 18))

    x = Bidirectional(
        LSTM(64, return_sequences=True)
    )(inputs)

    attention_output = Attention()([x, x])

    x = GlobalAveragePooling1D()(attention_output)
    x = Dropout(0.2)(x)
    x = Dense(32, activation="relu")(x)

    outputs = Dense(1)(x)

    model = Model(inputs, outputs)

    return model