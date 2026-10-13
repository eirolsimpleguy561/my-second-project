import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

CLASS_NAMES = ['airplane','automobile','bird','cat','deer',
               'dog','frog','horse','ship','truck']


def build_model():
    model = models.Sequential([
        layers.Conv2D(32, (3,3), activation='relu', input_shape=(32,32,3)),
        layers.MaxPooling2D((2,2)),
        layers.Conv2D(64, (3,3), activation='relu'),
        layers.MaxPooling2D((2,2)),
        layers.Conv2D(64, (3,3), activation='relu'),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(10, activation='softmax')
    ])
    return model


def main():
    # Load CIFAR-10 dataset
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0  # Normalize

    model = build_model()
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    print("Training model...")
    model.fit(x_train, y_train, epochs=10, validation_split=0.1, batch_size=64)

    test_loss, test_acc = model.evaluate(x_test, y_test)
    print(f"\nTest Accuracy: {test_acc:.4f}")

    # Save model
    model.save('cifar10_cnn.h5')
    print("Model saved to cifar10_cnn.h5")

    # Example prediction
    img = x_test[0:1]
    pred = model.predict(img)
    print(f"Predicted class: {CLASS_NAMES[np.argmax(pred[0])]}")


if __name__ == "__main__":
    main()
